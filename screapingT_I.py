# ================================================
#  INSTAGRAM SCRAPER | Clean Code
#  Libreria: instagrapi | Autor: koala60467
# ================================================

from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import time

DIAS = {0:"Lunes",1:"Martes",2:"Miercoles",3:"Jueves",4:"Viernes",5:"Sabado",6:"Domingo"}

# ================================================
#  CONEXION
# ================================================

def conectar() -> Client:
    """Autentica en Instagram con cookies del navegador"""
    try:
        cl = Client()
        cl.set_settings({"cookies": {
            "sessionid":  input("🔑 sessionid:  ").strip(),
            "csrftoken":  input("🔑 csrftoken:  ").strip(),
            "ds_user_id": input("🔑 ds_user_id: ").strip()
        }})
        cl.login_by_sessionid(cl.get_settings()["cookies"]["sessionid"])
        print("✅ Autenticado como: @koala60467")
        return cl
    except (LoginRequired, ClientError) as e:
        print(f"❌ Error: {e}"); return None


# ================================================
#  EXTRACCION
# ================================================

def extraer_perfil(cl: Client, username: str) -> dict:
    """Obtiene datos del perfil"""
    time.sleep(2)
    raw = cl.user_info(cl.user_id_from_username(username))
    return {
        "username":   raw.username,
        "nombre":     raw.full_name      or "Sin nombre",
        "biografia":  raw.biography      or "Sin biografia",
        "seguidores": raw.follower_count,
        "siguiendo":  raw.following_count,
        "posts":      raw.media_count,
        "verificado": raw.is_verified
    }

def extraer_posts(cl: Client, username: str, cantidad: int) -> list:
    """Obtiene los ultimos posts del perfil"""
    time.sleep(3)
    medias = cl.user_medias(cl.user_id_from_username(username), cantidad)
    return [{
        "fecha":       m.taken_at.strftime('%d/%m/%Y'),
        "hora":        m.taken_at.hour,
        "dia":         DIAS[m.taken_at.weekday()],
        "likes":       m.like_count,
        "comentarios": m.comment_count,
        "tipo":        "Video" if m.media_type == 2 else "Foto",
        "url":         f"instagram.com/p/{m.code}/"
    } for m in medias]


# ================================================
#  ANALISIS
# ================================================

def calcular_analisis(perfil: dict, posts: list) -> dict:
    """Calcula metricas de engagement"""
    likes = sum(p["likes"] for p in posts)
    coms  = sum(p["comentarios"] for p in posts)
    return {
        "engagement":    round((likes + coms) / perfil["seguidores"] * 100, 2) if perfil["seguidores"] else 0,
        "prom_likes":    round(likes / len(posts), 2),
        "prom_coms":     round(coms  / len(posts), 2),
        "mejor_post":    max(posts, key=lambda p: p["likes"]),
        "tipo_principal":    "Foto" if sum(1 for p in posts if p["tipo"]=="Foto") >= len(posts)/2 else "Video",
        "total_likes":   likes,
        "total_coms":    coms
    }

def calcular_horario(posts: list) -> dict:
    """Calcula mejor hora y dia para hacer lives"""
    por_hora = defaultdict(list)
    por_dia  = defaultdict(list)

    for p in posts:
        eng = p["likes"] + p["comentarios"]
        por_hora[p["hora"]].append(eng)
        por_dia[p["dia"]].append(eng)

    prom_hora  = {h: round(sum(v)/len(v), 2) for h, v in por_hora.items()}
    prom_dia   = {d: round(sum(v)/len(v), 2) for d, v in por_dia.items()}
    mejor_hora = max(prom_hora, key=prom_hora.get)
    mejor_dia  = max(prom_dia,  key=prom_dia.get)
    franja     = "manana" if mejor_hora < 12 else "mediodia" if mejor_hora < 17 else "tarde" if mejor_hora < 20 else "noche"

    return {
        "mejor_hora":  mejor_hora,
        "mejor_dia":   mejor_dia,
        "prom_hora":   prom_hora,
        "prom_dia":    prom_dia,
        "recomendacion": f"Haz tus lives los {mejor_dia}s a las {mejor_hora}:00h ({franja})"
    }


# ================================================
#  MOSTRAR
# ================================================

def mostrar(perfil, posts, analisis, horario):
    """Muestra todos los resultados en consola"""
    nivel = "🔥 Excelente" if analisis["engagement"] >= 6 else "✅ Bueno" if analisis["engagement"] >= 3 else "⚠️ Normal" if analisis["engagement"] >= 1 else "❌ Bajo"

    print(f"\n{'='*48}\n  📊 @{perfil['username']}\n{'='*48}")
    print(f"  👥 Seguidores: {perfil['seguidores']:,} | ➡️  Siguiendo: {perfil['siguiendo']:,}")
    print(f"  📸 Posts: {perfil['posts']:,} | ✅ Verificado: {'Si' if perfil['verificado'] else 'No'}")

    print(f"\n  📌 {len(posts)} posts:")
    for i, p in enumerate(posts, 1):
        print(f"   {i}. ❤️{p['likes']:,} | 💬{p['comentarios']:,} | {p['tipo']} | {p['dia']} {p['hora']}:00h")

    print(f"\n  📈 Engagement: {analisis['engagement']}% {nivel}")
    print(f"  ❤️  Prom likes: {analisis['prom_likes']:,} | 💬 Prom coment: {analisis['prom_coms']:,}")
    print(f"  🏆 Mejor post: {analisis['mejor_post']['likes']:,} likes ({analisis['mejor_post']['fecha']})")

    print(f"\n  🕐 HORARIO OPTIMO PARA LIVES")
    print(f"  📅 Mejor dia: {horario['mejor_dia']} | 🕐 Mejor hora: {horario['mejor_hora']}:00h")
    print(f"  🎯 {horario['recomendacion']}")

    print(f"\n  📊 Engagement por hora:")
    for h, e in sorted(horario["prom_hora"].items()):
        print(f"     {h:02d}:00h {'█' * int(e/max(horario['prom_hora'].values())*15)} {e}")


# ================================================
#  EXPORTACION
# ================================================

def guardar_excel(perfil, posts, analisis, horario):
    """Guarda datos en Excel con 4 hojas"""
    with pd.ExcelWriter(f"{perfil['username']}.xlsx", engine="openpyxl") as w:
        pd.DataFrame([perfil]).to_excel(w, sheet_name="Perfil",   index=False)
        pd.DataFrame(posts).to_excel(w,   sheet_name="Posts",    index=False)
        pd.DataFrame([{"Engagement":analisis["engagement"],"Prom Likes":analisis["prom_likes"],
                        "Prom Comentarios":analisis["prom_coms"]}]).to_excel(w, sheet_name="Analisis", index=False)
        pd.DataFrame([{"Mejor Hora":f"{horario['mejor_hora']}:00h",
                        "Mejor Dia":horario["mejor_dia"],"Recomendacion":horario["recomendacion"]
                      }]).to_excel(w, sheet_name="Horario", index=False)
    print(f"✅ Excel: {perfil['username']}.xlsx")

def generar_graficas(perfil, posts, analisis, horario):
    """Genera 6 graficas de analisis"""
    et   = [f"P{i+1}" for i in range(len(posts))]
    fig, ax = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f"@{perfil['username']} - Instagram", fontsize=14, fontweight="bold")

    ax[0,0].bar(et, [p["likes"] for p in posts],       color="#E1306C"); ax[0,0].set_title("❤️ Likes")
    ax[0,1].bar(et, [p["comentarios"] for p in posts], color="#405DE6"); ax[0,1].set_title("💬 Comentarios")

    fotos  = sum(1 for p in posts if p["tipo"]=="Foto")
    ax[0,2].pie([fotos, len(posts)-fotos], labels=[f"Fotos({fotos})",f"Videos({len(posts)-fotos})"],
                colors=["#E1306C","#405DE6"], autopct="%1.1f%%"); ax[0,2].set_title("📸 Tipos")

    horas = sorted(horario["prom_hora"].keys())
    ax[1,0].bar(horas, [horario["prom_hora"][h] for h in horas], color="#FCAF45")
    ax[1,0].axvline(x=horario["mejor_hora"], color="red", linestyle="--", label=f"{horario['mejor_hora']}:00h")
    ax[1,0].set_title("🕐 Engagement por hora"); ax[1,0].legend()

    dias = list(horario["prom_dia"].keys())
    ax[1,1].bar(dias, [horario["prom_dia"][d] for d in dias], color="#833AB4")
    ax[1,1].set_title("📅 Engagement por dia"); ax[1,1].tick_params(axis="x", rotation=30)

    ax[1,2].barh(["Engagement%","Prom.Likes","Prom.Coment"],
                 [analisis["engagement"],analisis["prom_likes"],analisis["prom_coms"]],
                 color=["#FCAF45","#E1306C","#405DE6"]); ax[1,2].set_title("📈 Resumen")

    plt.tight_layout()
    plt.savefig(f"{perfil['username']}_graficas.png", dpi=150)
    plt.show()
    print(f"✅ Graficas: {perfil['username']}_graficas.png")


# ================================================
#  MAIN
# ================================================

def main():
    print("="*48)
    print("  INSTAGRAM SCRAPER | Clean Code")
    print("  instagrapi | koala60467")
    print("="*48)

    cl = conectar()
    if not cl: return

    objetivo = input("\n🔍 Usuario: ").strip().replace("@","")
    print("\n1. 3 posts   2. 10 posts   3. Ambos")
    opcion = input("Elige (1/2/3): ").strip()

    perfil = extraer_perfil(cl, objetivo)

    if opcion == "3":
        print("\n📌 Top 3:"); mostrar(perfil, extraer_posts(cl, objetivo, 3), calcular_analisis(perfil, extraer_posts(cl, objetivo, 3)), calcular_horario(extraer_posts(cl, objetivo, 3)))

    cantidad = 3 if opcion == "1" else 10
    posts    = extraer_posts(cl, objetivo, cantidad)
    analisis = calcular_analisis(perfil, posts)
    horario  = calcular_horario(posts)

    mostrar(perfil, posts, analisis, horario)

    print("\n1. Excel   2. Graficas   3. Todo")
    exp = input("Exportar (1/2/3): ").strip()
    if exp in ["1","3"]: guardar_excel(perfil, posts, analisis, horario)
    if exp in ["2","3"]: generar_graficas(perfil, posts, analisis, horario)

    print(f"\n🚀 Listo: @{perfil['username']}")


if __name__ == "__main__":
    main()