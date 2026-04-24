# ================================================
#  INSTAGRAM SCRAPER | Modo Viral (Top 10 posts)
#  Libreria: instagrapi
# ================================================

# ── IMPORTACIONES ─────────────────────────────────
from instagrapi import Client
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import time

DIAS = {0:"Lunes",1:"Martes",2:"Miercoles",3:"Jueves",4:"Viernes",5:"Sabado",6:"Domingo"}


# ── CONEXION ─────────────────────────────────────
def conectar() -> Client:
    """Autentica con cookies del navegador"""
    cl = Client()
    cookies = {
        "sessionid":  input("🔑 sessionid: ").strip(),
        "csrftoken":  input("🔑 csrftoken: ").strip(),
        "ds_user_id": input("🔑 ds_user_id: ").strip()
    }
    cl.set_settings({"cookies": cookies})
    cl.login_by_sessionid(cookies["sessionid"])
    print("✅ Conectado")
    return cl


# ── EXTRACCION (SOLO TOP 10) ─────────────────────
def extraer_top10(cl: Client, username: str) -> tuple:
    """
    Estrategia: 
    1. Obtiene 50 posts, los ordena por likes+comentarios
    2. Se queda solo con los 10 mejores
    3. Extrae comentarios REALES solo de esos 10
    """
    uid = cl.user_id_from_username(username)
    perfil = cl.user_info(uid)
    
    print("📡 Analizando 50 posts para encontrar los 10 más virales...")
    todos = []
    for media in cl.user_medias(uid, 50):
        # 🔗 IMPORTANTE: Cada post tiene un código único (ej: "CxYZ123")
        # El link completo es: instagram.com/p/CODIGO/
        link = f"https://www.instagram.com/p/{media.code}/"
        
        todos.append({
            "id": media.id,
            "link": link,  # ← NUEVO: Guarda el link del post
            "fecha": media.taken_at.strftime('%d/%m/%Y'),
            "hora": media.taken_at.hour,
            "dia": DIAS[media.taken_at.weekday()],
            "likes": media.like_count,
            "coms": media.comment_count,
            "tipo": "Video" if media.media_type == 2 else "Foto",
            "score": media.like_count + media.comment_count
        })
        time.sleep(0.5)
    
    # Ordenar y quedarse con top 10
    top10 = sorted(todos, key=lambda x: x["score"], reverse=True)[:10]
    
    print(f"🏆 Extrayendo comentarios de los 10 posts más populares...")
    for post in top10:
        try:
            comentarios = [f"@{c.user.username}: {c.text}" 
                          for c in cl.media_comments(post["id"], amount=3)]
            post["top_comments"] = comentarios
        except:
            post["top_comments"] = []
        time.sleep(1)
    
    return perfil, top10


# ── ANALISIS ─────────────────────────────────────
def analizar(perfil, posts: list) -> dict:
    """Calcula engagement y mejor horario basado en los top 10 posts"""
    
    total_likes = sum(p["likes"] for p in posts)
    total_coms = sum(p["coms"] for p in posts)
    eng = round((total_likes + total_coms) / perfil.follower_count * 100, 2) if perfil.follower_count else 0
    
    por_hora = defaultdict(list)
    por_dia = defaultdict(list)
    
    for p in posts:
        e = p["likes"] + p["coms"]
        por_hora[p["hora"]].append(e)
        por_dia[p["dia"]].append(e)
    
    prom_hora = {h: sum(v)/len(v) for h, v in por_hora.items()}
    prom_dia = {d: sum(v)/len(v) for d, v in por_dia.items()}
    
    mejor_hora = max(prom_hora, key=prom_hora.get) if prom_hora else 12
    mejor_dia = max(prom_dia, key=prom_dia.get) if prom_dia else "Sábado"
    
    if mejor_hora < 12: franja = "mañana 🌅"
    elif mejor_hora < 17: franja = "mediodía ☀️"
    elif mejor_hora < 20: franja = "tarde 🌤️"
    else: franja = "noche 🌙"
    
    return {
        "engagement": eng,
        "prom_likes": round(total_likes/10, 2),
        "prom_coms": round(total_coms/10, 2),
        "mejor_post": max(posts, key=lambda p: p["likes"]),
        "mejor_hora": mejor_hora,
        "mejor_dia": mejor_dia,
        "recomendacion": f"📈 Publica los {mejor_dia}s a las {mejor_hora}:00h ({franja})",
        "prom_hora": prom_hora,
        "prom_dia": prom_dia
    }


# ── MOSTRAR RESULTADOS ───────────────────────────
def mostrar(perfil, posts: list, stats: dict):
    """Muestra los 10 posts más virales con sus comentarios y links"""
    
    nivel = ("🔥 Excelente" if stats["engagement"] >= 6 
             else "✅ Bueno" if stats["engagement"] >= 3 
             else "⚠️ Normal" if stats["engagement"] >= 1 
             else "❌ Bajo")
    
    print(f"\n{'='*52}")
    print(f"  📊 @{perfil.username} - TOP 10 POSTS MÁS VIRALES")
    print(f"{'='*52}")
    print(f"  👤 {perfil.full_name or 'Sin nombre'}")
    print(f"  👥 {perfil.follower_count:,} seguidores")
    print(f"  📸 {perfil.media_count} posts totales")
    
    print(f"\n  🏆 LOS 10 MEJORES POSTS:")
    for i, p in enumerate(posts, 1):
        print(f"\n   {i}. ❤️ {p['likes']:,} | 💬 {p['coms']} | {p['tipo']} | {p['dia']} {p['hora']}:00h")
        print(f"      🔗 {p['link']}")  # ← NUEVO: Muestra el link en consola también
        for c in p["top_comments"][:2]:
            print(f"      💬 {c[:70]}")
    
    print(f"\n  📈 Engagement Rate: {stats['engagement']}% {nivel}")
    print(f"  ❤️ Promedio likes (top10): {stats['prom_likes']}")
    print(f"  💬 Promedio comentarios (top10): {stats['prom_coms']}")
    print(f"\n  🎯 {stats['recomendacion']}")
    
    if stats["prom_hora"]:
        max_e = max(stats["prom_hora"].values())
        print("\n  📊 Engagement por hora (basado en posts virales):")
        for h in range(24):
            if h in stats["prom_hora"]:
                barra = '█' * int(stats["prom_hora"][h] / max_e * 15)
                print(f"     {h:02d}:00h {barra} {stats['prom_hora'][h]:.0f}")
            else:
                print(f"     {h:02d}:00h (sin datos)")


# ── EXPORTAR ─────────────────────────────────────
def exportar(perfil, posts: list, stats: dict):
    """Guarda los 10 posts virales en Excel con sus links"""
    username = perfil.username
    
    # Prepara datos para Excel (incluyendo el link)
    posts_exp = []
    for p in posts:
        copia = p.copy()
        # Convierte lista de comentarios a string
        copia["top_comments"] = " | ".join(p["top_comments"][:3])
        # Elimina campos innecesarios (pero CONSERVA el "link")
        copia.pop("id", None)
        copia.pop("score", None)
        posts_exp.append(copia)
    
    # Guarda en Excel con múltiples hojas
    with pd.ExcelWriter(f"{username}_top10.xlsx", engine="openpyxl") as w:
        # Hoja de resumen
        pd.DataFrame([{
            "Usuario": username,
            "Nombre": perfil.full_name,
            "Seguidores": perfil.follower_count,
            "Engagement": stats["engagement"],
            "Promedio_Likes": stats["prom_likes"],
            "Promedio_Comentarios": stats["prom_coms"],
            "Mejor_Hora": f"{stats['mejor_hora']}:00h",
            "Mejor_Dia": stats["mejor_dia"],
            "Recomendacion": stats["recomendacion"]
        }]).to_excel(w, sheet_name="Resumen", index=False)
        
        # Hoja de los 10 posts con LINKS incluidos
        pd.DataFrame(posts_exp).to_excel(w, sheet_name="Top10_Posts", index=False)
    
    # Gráficas
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f"@{username} - Análisis de los 10 posts más virales", fontsize=14)
    
    scores = [p["score"] for p in posts]
    ax1.bar(range(1, 11), scores, color="#E1306C")
    ax1.set_title("Engagement de los Top 10 Posts")
    ax1.set_xlabel("Rango (1 = más viral)")
    ax1.set_ylabel("Likes + Comentarios")
    
    if stats["prom_hora"]:
        horas = sorted(stats["prom_hora"].keys())
        valores = [stats["prom_hora"][h] for h in horas]
        ax2.plot(horas, valores, marker="o", color="#405DE6", linewidth=2)
        ax2.axvline(x=stats["mejor_hora"], color="red", linestyle="--", 
                   label=f"Mejor hora: {stats['mejor_hora']}:00h")
        ax2.set_title("Horario óptimo para contenido viral")
        ax2.set_xlabel("Hora del día")
        ax2.set_ylabel("Engagement promedio")
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{username}_top10_graficas.png", dpi=150)
    plt.show()
    
    print(f"✅ Exportado: {username}_top10.xlsx")
    print(f"   → Los links de cada post están en la columna 'link' del Excel")
    print(f"✅ Gráficas: {username}_top10_graficas.png")


# ── MAIN ─────────────────────────────────────────
def main():
    """Flujo principal: conecta, extrae top 10, analiza, muestra y exporta"""
    print("="*52)
    print("  INSTAGRAM SCRAPER | Modo: Top 10 Posts Virales")
    print("="*52)
    
    cl = conectar()
    usuario = input("\n🔍 Usuario a analizar: ").strip().replace("@", "")
    
    print(f"\n📡 Buscando los 10 mejores posts de @{usuario}...")
    perfil, posts = extraer_top10(cl, usuario)
    stats = analizar(perfil, posts)
    mostrar(perfil, posts, stats)
    
    if input("\n📁 ¿Exportar a Excel y gráficas? (s/n): ").lower() == "s":
        exportar(perfil, posts, stats)
    
    print(f"\n🚀 Análisis completado: 10 posts virales identificados")
    print(f"💡 El post con más likes tuvo {stats['mejor_post']['likes']:,} likes")
    print(f"🔗 Los links están guardados en el Excel para que los puedas visitar")


if __name__ == "__main__":
    main()