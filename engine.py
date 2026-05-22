import os
import itertools
import json
import requests
from datetime import datetime

# ==========================================
# 1. THE EMBEDDED HTML MATCH VISUAL TEMPLATE
# ==========================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{PLAYER_A}} vs {{PLAYER_B}} Advanced Stats, Fantasy Form & Debate Matrix</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <meta name="google-site-verification" content="c_K6M_6ZUJTCpaExzxn5HyzwgyupoiwBwC2TUBi5RRg" />
</head>
<body class="bg-slate-900 text-slate-100 font-sans min-h-screen">

    <header class="border-b border-slate-800 bg-slate-950 p-4 sticky top-0 z-50">
        <div class="max-w-6xl mx-auto flex justify-between items-center">
            <span class="text-xl font-black tracking-wider text-emerald-400">📊 DEBATE.FC</span>
            <span class="text-xs text-slate-400 bg-slate-800 px-2 py-1 rounded">Auto-Updated Daily</span>
        </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-8">
        <div class="text-center mb-10">
            <h1 class="text-3xl md:text-5xl font-extrabold tracking-tight mb-2">
                <span class="text-emerald-400">{{PLAYER_A}}</span> 
                <span class="text-slate-500 text-2xl md:text-3xl font-normal mx-2">vs</span> 
                <span class="text-cyan-400">{{PLAYER_B}}</span>
            </h1>
            <p class="text-slate-400 text-sm md:text-base">Data-backed performance metric comparison & FPL decision matrix.</p>
        </div>

        <!-- FPL Recommendation Matrix -->
        <div class="bg-gradient-to-r from-emerald-950 to-slate-900 border border-emerald-500/30 rounded-xl p-6 mb-8 shadow-xl">
            <div class="flex items-center gap-2 mb-3">
                <span class="flex h-3 w-3 relative">
                    <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span class="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                </span>
                <h2 class="text-xs font-bold uppercase tracking-widest text-emerald-400">Data-Engine Verdict</h2>
            </div>
            <p class="text-lg font-medium text-slate-200">{{VERDICT_TEXT}}</p>
        </div>

        <!-- Performance Bars Matrix -->
        <div class="bg-slate-950 border border-slate-800 rounded-xl p-6 mb-8 shadow-md">
            <h3 class="text-sm font-bold uppercase tracking-widest text-slate-400 mb-6 border-b border-slate-800 pb-2">Key Performance Indicators (Per 90 mins)</h3>
            
            <div class="space-y-6">
                <!-- Stat Item: Goals -->
                <div>
                    <div class="flex justify-between text-sm mb-1 font-semibold">
                        <span class="text-emerald-400">{{PLAYER_A_G}}</span>
                        <span class="text-slate-400 font-normal uppercase tracking-wider text-xs">Goals</span>
                        <span class="text-cyan-400">{{PLAYER_B_G}}</span>
                    </div>
                    <div class="flex h-3 bg-slate-800 rounded-full overflow-hidden">
                        <div class="bg-emerald-500" style="width: {{PLAYER_A_G_PCT}}%"></div>
                        <div class="bg-cyan-500 ml-auto" style="width: {{PLAYER_B_G_PCT}}%"></div>
                    </div>
                </div>

                <!-- Stat Item: Assists -->
                <div>
                    <div class="flex justify-between text-sm mb-1 font-semibold">
                        <span class="text-emerald-400">{{PLAYER_A_A}}</span>
                        <span class="text-slate-400 font-normal uppercase tracking-wider text-xs">Assists</span>
                        <span class="text-cyan-400">{{PLAYER_B_A}}</span>
                    </div>
                    <div class="flex h-3 bg-slate-800 rounded-full overflow-hidden">
                        <div class="bg-emerald-500" style="width: {{PLAYER_A_A_PCT}}%"></div>
                        <div class="bg-cyan-500 ml-auto" style="width: {{PLAYER_B_A_PCT}}%"></div>
                    </div>
                </div>

                <!-- Stat Item: Expected Goals (xG) -->
                <div>
                    <div class="flex justify-between text-sm mb-1 font-semibold">
                        <span class="text-emerald-400">{{PLAYER_A_XG}}</span>
                        <span class="text-slate-400 font-normal uppercase tracking-wider text-xs">Expected Goals (xG)</span>
                        <span class="text-cyan-400">{{PLAYER_B_XG}}</span>
                    </div>
                    <div class="flex h-3 bg-slate-800 rounded-full overflow-hidden">
                        <div class="bg-emerald-500" style="width: {{PLAYER_A_XG_PCT}}%"></div>
                        <div class="bg-cyan-500 ml-auto" style="width: {{PLAYER_B_XG_PCT}}%"></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="text-center text-xs text-slate-500 mt-12">
            <p>Data scraped natively from open-source registries. Last compilation execution: {{TIMESTAMP}}</p>
            <p class="mt-2">Generated by DEBATE.FC Programmatic Network Engine.</p>
        </div>
    </main>
</body>
</html>
"""

# ==========================================
# 2. THE LIVE API INGESTION ENGINE
# ==========================================
def fetch_live_fpl_pool():
    print("Connecting to live Premier League data registries...")
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Connection error: {e}. Utilizing local sandbox data pool instead.")
        return []

    all_players = data.get("elements", [])
    processed_players = []
    
    # Filter for active Midfielders (3) and Forwards (4) with significant match minutes
    for p in all_players:
        minutes = p.get("minutes", 0)
        if p.get("element_type") in [3, 4] and minutes > 500:
            match_segments = minutes / 90.0
            
            goals_per_90 = round(p.get("goals_scored", 0) / match_segments, 2)
            assists_per_90 = round(p.get("assists", 0) / match_segments, 2)
            
            try:
                xg_total = float(p.get("expected_goals", 0))
                xg_per_90 = round(xg_total / match_segments, 2)
            except (ValueError, TypeError):
                xg_per_90 = 0.0

            processed_players.append({
                "name": p.get("web_name"),
                "goals": goals_per_90,
                "assists": assists_per_90,
                "xg": xg_per_90,
                "total_points": p.get("total_points", 0)
            })

    # Slice out the top 25 high-performing profiles to maximize long-tail search matrix density
    return sorted(processed_players, key=lambda x: x["total_points"], reverse=True)[:25]


# ==========================================
# 3. MATRIX COMPILER & GENERATOR LOGIC
# ==========================================
def clean_url_slug(name):
    return name.lower().replace(" ", "-").replace(".", "").replace("'", "")

def execute_matrix_pipeline():
    os.makedirs('public/vs', exist_ok=True)
    
    players_pool = fetch_live_fpl_pool()
    if not players_pool:
        print("Data ingestion empty. Execution pipeline suspended.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    generated_links = []

    # Cross-pair every single player programmatically
    for player_a, player_b in itertools.combinations(players_pool, 2):
        slug_a = clean_url_slug(player_a['name'])
        slug_b = clean_url_slug(player_b['name'])
        filename = f"{slug_a}-vs-{slug_b}.html"
        filepath = os.path.join('public/vs', filename)
        
        # Calculate visualization bar ratios cleanly
        total_g = (player_a['goals'] + player_b['goals']) or 1.0
        total_a = (player_a['assists'] + player_b['assists']) or 1.0
        total_xg = (player_a['xg'] + player_b['xg']) or 1.0
        
        # Algorithmic verdict text engine
        if player_a['goals'] > player_b['goals'] and player_a['xg'] > player_b['xg']:
            verdict = f"<strong>{player_a['name']}</strong> is currently outperforming in structural goal conversion and taking higher quality shooting opportunities."
        elif player_b['goals'] > player_a['goals'] and player_b['xg'] > player_a['xg']:
            verdict = f"<strong>{player_b['name']}</strong> claims the analytical edge here, showing superior clinical output per 90 minutes."
        else:
            verdict = f"A highly balanced data matchup. <strong>{player_a['name']}</strong> provides different operational performance attributes compared to <strong>{player_b['name']}</strong>."

        # Execute safe block replacements inside our template string variables
        replacements = {
            '{{PLAYER_A}}': player_a['name'],
            '{{PLAYER_B}}': player_b['name'],
            '{{VERDICT_TEXT}}': verdict,
            '{{PLAYER_A_G}}': f"{player_a['goals']:.2f}",
            '{{PLAYER_B_G}}': f"{player_b['goals']:.2f}",
            '{{PLAYER_A_G_PCT}}': f"{(player_a['goals'] / total_g) * 100:.1f}",
            '{{PLAYER_B_G_PCT}}': f"{(player_b['goals'] / total_g) * 100:.1f}",
            '{{PLAYER_A_A}}': f"{player_a['assists']:.2f}",
            '{{PLAYER_B_A}}': f"{player_b['assists']:.2f}",
            '{{PLAYER_A_A_PCT}}': f"{(player_a['assists'] / total_a) * 100:.1f}",
            '{{PLAYER_B_A_PCT}}': f"{(player_b['assists'] / total_a) * 100:.1f}",
            '{{PLAYER_A_XG}}': f"{player_a['xg']:.2f}",
            '{{PLAYER_B_XG}}': f"{player_b['xg']:.2f}",
            '{{PLAYER_A_XG_PCT}}': f"{(player_a['xg'] / total_xg) * 100:.1f}",
            '{{PLAYER_B_XG_PCT}}': f"{(player_b['xg'] / total_xg) * 100:.1f}",
            '{{TIMESTAMP}}': timestamp
        }
        
        compiled_page = HTML_TEMPLATE
        for placeholder, value in replacements.items():
            compiled_page = compiled_page.replace(placeholder, value)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(compiled_page)
            
        generated_links.append({
            'anchor_text': f"{player_a['name']} vs {player_b['name']}",
            'url': f"vs/{filename}"
        })

    # Compile the central directory discovery landing page (public/index.html)
    build_central_index(generated_links, timestamp)

def build_central_index(links, timestamp):
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DEBATE.FC | Head-to-Head Player Analytics Engine</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; max-width: 900px; margin: 40px auto; padding: 0 20px; }}
        h1 {{ color: #34d399; text-align: center; font-size: 2.5rem; font-weight: 900; letter-spacing: -0.025em; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; margin-top: 40px; }}
        .card {{ background: #1e293b; padding: 14px; border-radius: 10px; text-align: center; border: 1px solid #334155; text-decoration: none; color: #f8fafc; font-weight: 500; transition: all 0.2s; }}
        .card:hover {{ border-color: #34d399; background: #1e293b; transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(52, 211, 153, 0.1); }}
        .footer {{ text-align: center; font-size: 0.8rem; color: #64748b; margin-top: 60px; border-top: 1px solid #334155; padding-top: 20px; }}
    </style>
</head>
<body>
    <h1>📊 DEBATE.FC DATA CORE</h1>
    <p style="text-align:center; color:#94a3b8;">Select a long-tail search matrix connection node below to inspect performance indicators.</p>
    <div class="grid">
    """
    for link in links:
        index_html += f'        <a class="card" href="{link["url"]}">{link["anchor_text"]}</a>\n'
        
    index_html += f"""    </div>
    <div class="footer">Site compiled automatically on {timestamp} UTC via Live API Infrastructure.</div>
</body>
</html>"""

    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
    print(f"Successfully generated main landing directory with {len(links)} long-tail nodes.")

if __name__ == "__main__":
    execute_matrix_pipeline()
