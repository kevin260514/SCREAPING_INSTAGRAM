# ================================================
#  TIKTOK SCRAPER | Clean Code (Versión Corregida)
#  Mismo enfoque que Instagram: Top 10 virales
# ================================================

from TikTokApi import TikTokApi
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
import asyncio
from datetime import datetime

DIAS = {0:"Lunes", 1:"Martes", 2:"Miercoles", 3:"Jueves", 4:"Viernes", 5:"Sabado", 6:"Domingo"}

# ================================================
#  CONEXIÓN CON TIKTOK (SIMPLIFICADA)
# ================================================

class TikTokAPI:
    async def conectar(self, ms_token: str):
        """Conecta usando msToken de TikTok"""
        self.api = TikTokApi()
        await self.api.create_sessions(ms_tokens=[ms_token], num_sessions=1, headless=True)
        print("✅ Conectado a TikTok")
    
    async def get_perfil(self, username: str):
        """Obtiene datos del perfil"""
        user = self.api.user(username=username)
        info = await user.info()
        return info["userInfo"]
    
    async def get_videos(self, username: str, cantidad: int):
        """Obtiene lista de videos"""
        videos = []
        user = self.api.user(username=username)
        async for v in user.videos(count=cantidad):
            videos.append(v.as_dict)
            await asyncio.sleep(0.3)
        return videos
    
    async def get_comentarios(self, video_id: str, cantidad: int = 3):
        """Obtiene comentarios de un video"""
        try:
            video = self.api.video(id=video_id)
            comentarios = []
            async for c in video.comments(count=cantidad):
                comentarios.append(f"@{c.user.username}: {c.text}")
                await asyncio.sleep(0.2)
            return comentarios
        except:
            return []
    
    async def cerrar(self):
        await self.api.close_sessions()

# ================================================
#  EXTRACCIÓN DE TOP 10 VIRALES
# ================================================

async def extraer_top10(api: TikTokAPI, username: str):
    """
    Extrae SOLO los 10 videos con más engagement
    Misma lógica que Instagram: analiza 50, se queda con top 10
    """
    
    # 1. Obtener perfil
    raw_perfil = await api.get_perfil(username)
    seguidores = raw_perfil["stats"]["followerCount"]
    print(f"📊 @{username} tiene {seguidores:,} seguidores")
    
    # 2. Analizar 50 videos
    print(f"📡 Analizando 50 videos para encontrar los 10 más virales...")
    raw_videos = await api.get_videos(username, 50)
    
    # 3. Calcular score de cada video
    todos = []
    for v in raw_videos:
        fecha = datetime.fromtimestamp(v["createTime"])
        stats = v["stats"]
        
        # Score = likes + comentarios + compartidos
        score = stats["diggCount"] + stats["commentCount"] + stats["shareCount"]
        
        todos.append({
            "id": v["id"],
            "link": f"https://www.tiktok.com/@{username}/video/{v['id']}",
            "fecha": fecha.strftime('%d/%m/%Y'),
            "hora": fecha.hour,
            "dia": DIAS[fecha.weekday()],
            "vistas": stats["playCount"],
            "likes": stats["diggCount"],
            "comentarios": stats["commentCount"],
            "compartidos": stats["shareCount"],
            "score": score
        })
        await asyncio.sleep(0.3)
    
    # 4. Ordenar y quedarse con TOP 10
    top10 = sorted(todos, key=lambda x: x["score"], reverse=True)[:10]
    
    # 5. Agregar comentarios SOLO a los top 10
    print(f"🏆 Extrayendo comentarios de los 10 videos más populares...")
    for video in top10:
        video["top_comments"] = await api.get_comentarios(video["id"], 3)
        await asyncio.sleep(0.5)
    
    return {
        "username": username,
        "seguidores": seguidores,
        "videos": top10
    }

# ================================================
#  ANÁLISIS (misma fórmula que Instagram)
# ================================================

def analizar(datos: dict):
    """Calcula engagement y mejor horario basado en top 10 videos"""
    
    videos = datos["videos"]
    seguidores = datos["seguidores"]
    
    # Engagement = (likes + comentarios + compartidos) / seguidores * 100
    total_likes = sum(v["likes"] for v in videos)
    total_coms = sum(v["comentarios"] for v in videos)
    total_shares = sum(v["compartidos"] for v in videos)
    
    engagement = round((total_likes + total_coms + total_shares) / seguidores * 100, 2) if seguidores else 0
    
    # Agrupar por hora y día
    por_hora = defaultdict(list)
    por_dia = defaultdict(list)
    
    for v in videos:
        eng = v["likes"] + v["comentarios"] + v["compartidos"]
        por_hora[v["hora"]].append(eng)
        por_dia[v["dia"]].append(eng)
    
    # Promedios
    prom_hora = {h: round(sum(val)/len(val), 2) for h, val in por_hora.items()}
    prom_dia = {d: round(sum(val)/len(val), 2) for d, val in por_dia.items()}
    
    # Mejor momento (max con key)
    mejor_hora = max(prom_hora, key=prom_hora.get) if prom_hora else 20
    mejor_dia = max(prom_dia, key=prom_dia.get) if prom_dia else "Sábado"
    
    # Clasificar franja
    if mejor_hora < 12: franja = "mañana 🌅"
    elif mejor_hora < 17: franja = "mediodía ☀️"
    elif mejor_hora < 20: franja = "tarde 🌤️"
    else: franja = "noche 🌙"
    
    return {
        "engagement": engagement,
        "prom_likes": round(total_likes / 10, 2),
        "prom_coms": round(total_coms / 10, 2),
        "prom_shares": round(total_shares / 10, 2),
        "mejor_video": max(videos, key=lambda v: v["likes"]),
        "mejor_hora": mejor_hora,
        "mejor_dia": mejor_dia,
        "recomendacion": f"📅 Publica los {mejor_dia}s a las {mejor_hora}:00h ({franja})",
        "prom_hora": prom_hora,
        "prom_dia": prom_dia
    }

# ================================================
#  MOSTRAR RESULTADOS
# ================================================

def mostrar(datos: dict, stats: dict):
    """Muestra los 10 videos virales con sus comentarios"""
    
    videos = datos["videos"]
    
    # Nivel de engagement
    if stats["engagement"] >= 6: nivel = "🔥 Excelente"
    elif stats["engagement"] >= 3: nivel = "✅ Bueno"
    elif stats["engagement"] >= 1: nivel = "⚠️ Normal"
    else: nivel = "❌ Bajo"
    
    print(f"\n{'='*52}")
    print(f"  🎵 @{datos['username']} - TOP 10 VIDEOS MÁS VIRALES")
    print(f"{'='*52}")
    print(f"  👥 {datos['seguidores']:,} seguidores")
    
    print(f"\n  🏆 TOP 10 VIDEOS:")
    for i, v in enumerate(videos, 1):
        print(f"\n   {i}. ❤️{v['likes']:,} | 💬{v['comentarios']} | 🔗{v['compartidos']} | 👀{v['vistas']:,}")
        print(f"      🔗 {v['link']}")
        print(f"      📅 {v['dia']} a las {v['hora']}:00h")
        for c in v["top_comments"][:2]:
            print(f"      💬 {c[:70]}")
    
    print(f"\n  📈 Engagement Rate: {stats['engagement']}% {nivel}")
    print(f"  ❤️ Promedio likes: {stats['prom_likes']:,}")
    print(f"  💬 Promedio comentarios: {stats['prom_coms']}")
    print(f"  🔗 Promedio compartidos: {stats['prom_shares']:,}")
    print(f"\n  🎯 {stats['recomendacion']}")
    
    # Mini gráfico de barras en consola
    if stats["prom_hora"]:
        max_e = max(stats["prom_hora"].values())
        print("\n  📊 Engagement por hora:")
        for h in range(24):
            if h in stats["prom_hora"]:
                barra = '█' * int(stats["prom_hora"][h] / max_e * 15)
                print(f"     {h:02d}:00h {barra} {stats['prom_hora'][h]:.0f}")
            else:
                print(f"     {h:02d}:00h (sin datos)")

# ================================================
#  EXPORTAR A EXCEL (con links)
# ================================================

def exportar_excel(datos: dict, stats: dict):
    """Guarda Excel con los links de los videos"""
    
    username = datos["username"]
    videos = datos["videos"]
    
    # Preparar datos para Excel
    datos_excel = []
    for i, v in enumerate(videos, 1):
        datos_excel.append({
            "Ranking": i,
            "Link": v["link"],  # ← Link clickeable
            "Vistas": v["vistas"],
            "Likes": v["likes"],
            "Comentarios": v["comentarios"],
            "Compartidos": v["compartidos"],
            "Fecha": v["fecha"],
            "Hora": f"{v['hora']}:00h",
            "Dia": v["dia"],
            "Score": v["score"],
            "Top_Comentarios": " | ".join(v["top_comments"][:3])
        })
    
    # Guardar Excel
    with pd.ExcelWriter(f"{username}_tiktok_top10.xlsx", engine="openpyxl") as writer:
        # Hoja de resumen
        pd.DataFrame([{
            "Usuario": username,
            "Seguidores": datos["seguidores"],
            "Engagement": stats["engagement"],
            "Prom_Likes": stats["prom_likes"],
            "Prom_Comentarios": stats["prom_coms"],
            "Prom_Compartidos": stats["prom_shares"],
            "Mejor_Hora": f"{stats['mejor_hora']}:00h",
            "Mejor_Dia": stats["mejor_dia"],
            "Recomendacion": stats["recomendacion"]
        }]).to_excel(writer, sheet_name="Resumen", index=False)
        
        # Hoja de top 10 videos
        pd.DataFrame(datos_excel).to_excel(writer, sheet_name="Top10_Videos", index=False)
    
    print(f"✅ Excel guardado: {username}_tiktok_top10.xlsx")
    print(f"   → Los links están en la columna 'Link'")

# ================================================
#  GENERAR GRÁFICAS
# ================================================

def generar_graficas(datos: dict, stats: dict):
    """Genera gráficas profesionales"""
    
    username = datos["username"]
    videos = datos["videos"]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"🎵 @{username} - Top 10 Videos más Virales (TikTok)", fontsize=14, fontweight="bold")
    
    # Gráfico 1: Score de los top 10
    scores = [v["score"] for v in videos]
    axes[0,0].bar(range(1, 11), scores, color="#FF0050")
    axes[0,0].set_title("🏆 Score de Engagement (Top 10)")
    axes[0,0].set_xlabel("Rango (1 = más viral)")
    axes[0,0].set_ylabel("Likes + Comentarios + Shares")
    
    # Gráfico 2: Engagement por hora
    if stats["prom_hora"]:
        horas = sorted(stats["prom_hora"].keys())
        valores = [stats["prom_hora"][h] for h in horas]
        axes[0,1].plot(horas, valores, marker="o", color="#00F2EA", linewidth=2)
        axes[0,1].axvline(x=stats["mejor_hora"], color="red", linestyle="--", 
                         label=f"Mejor hora: {stats['mejor_hora']}:00h")
        axes[0,1].set_title("🕐 Engagement por Hora")
        axes[0,1].set_xlabel("Hora del día")
        axes[0,1].set_ylabel("Engagement promedio")
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
    
    # Gráfico 3: Engagement por día
    if stats["prom_dia"]:
        dias = list(stats["prom_dia"].keys())
        valores_dia = [stats["prom_dia"][d] for d in dias]
        axes[1,0].bar(dias, valores_dia, color="#833AB4")
        axes[1,0].set_title("📅 Engagement por Día")
        axes[1,0].tick_params(axis="x", rotation=45)
    
    # Gráfico 4: Comparativa de métricas
    axes[1,1].barh(["Engagement %", "Likes (K)", "Comentarios", "Shares (K)"],
                   [stats["engagement"], stats["prom_likes"]/1000, stats["prom_coms"], stats["prom_shares"]/1000],
                   color=["#FF0050", "#00F2EA", "#833AB4", "#FCAF45"])
    axes[1,1].set_title("📊 Resumen de Métricas")
    
    plt.tight_layout()
    plt.savefig(f"{username}_tiktok_top10.png", dpi=150)
    plt.show()
    print(f"✅ Gráficas guardadas: {username}_tiktok_top10.png")

# ================================================
#  PROGRAMA PRINCIPAL
# ================================================

async def main():
    print("="*52)
    print("  TIKTOK SCRAPER | Top 10 Videos Virales")
    print("  Mismo enfoque que Instagram")
    print("="*52)
    print("\n📋 CÓMO OBTENER EL msToken:")
    print("   1. Abre tiktok.com en Chrome")
    print("   2. Presiona F12 → Application")
    print("   3. Cookies → https://www.tiktok.com")
    print("   4. Copia el valor de 'msToken'")
    print("-"*52)
    
    # Autenticación
    ms_token = input("\n🔑 msToken: ").strip()
    
    api = TikTokAPI()
    await api.conectar(ms_token)
    
    # Usuario
    usuario = input("\n🔍 Usuario a analizar: ").strip().replace("@", "")
    
    # Extraer top 10 virales
    datos = await extraer_top10(api, usuario)
    
    # Analizar
    stats = analizar(datos)
    
    # Mostrar resultados
    mostrar(datos, stats)
    
    # Exportar
    opcion = input("\n📁 ¿Exportar? (1=Excel, 2=Gráficas, 3=Ambos, 4=Nada): ").strip()
    
    if opcion in ["1", "3"]:
        exportar_excel(datos, stats)
    if opcion in ["2", "3"]:
        generar_graficas(datos, stats)
    
    # Cerrar
    await api.cerrar()
    print(f"\n🚀 Análisis completado: @{datos['username']}")
    print(f"💡 El video con más likes tuvo {stats['mejor_video']['likes']:,} likes")

if __name__ == "__main__":
    asyncio.run(main())