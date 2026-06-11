import json
import re
import pandas as pd

TEAM_FLAGS = {
    'Algeria': 'DZ',
    'Argentina': 'AR',
    'Australia': 'AU',
    'Austria': 'AT',
    'Belgium': 'BE',
    'Bosnia and Herzegovina': 'BA',
    'Brazil': 'BR',
    'Canada': 'CA',
    'Cape Verde': 'CV',
    'Colombia': 'CO',
    'Croatia': 'HR',
    'Curaçao': 'CW',
    'Czech Republic': 'CZ',
    'DR Congo': 'CD',
    'Ecuador': 'EC',
    'Egypt': 'EG',
    'England': 'GB',
    'France': 'FR',
    'Germany': 'DE',
    'Ghana': 'GH',
    'Haiti': 'HT',
    'Iran': 'IR',
    'Iraq': 'IQ',
    'Ivory Coast': 'CI',
    'Japan': 'JP',
    'Jordan': 'JO',
    'Mexico': 'MX',
    'Morocco': 'MA',
    'Netherlands': 'NL',
    'New Zealand': 'NZ',
    'Norway': 'NO',
    'Panama': 'PA',
    'Paraguay': 'PY',
    'Portugal': 'PT',
    'Qatar': 'QA',
    'Saudi Arabia': 'SA',
    'Scotland': 'GB',
    'Senegal': 'SN',
    'South Africa': 'ZA',
    'South Korea': 'KR',
    'Spain': 'ES',
    'Sweden': 'SE',
    'Switzerland': 'CH',
    'Tunisia': 'TN',
    'Turkey': 'TR',
    'United States': 'US',
    'Uruguay': 'UY',
    'Uzbekistan': 'UZ',
}
TEAM_CODES = {
    'Algeria': 'ALG',
    'Argentina': 'ARG',
    'Australia': 'AUS',
    'Austria': 'AUT',
    'Belgium': 'BEL',
    'Bosnia and Herzegovina': 'BIH',
    'Brazil': 'BRA',
    'Canada': 'CAN',
    'Cape Verde': 'CPV',
    'Colombia': 'COL',
    'Croatia': 'CRO',
    'Curaçao': 'CUW',
    'Czech Republic': 'CZE',
    'DR Congo': 'COD',
    'Ecuador': 'ECU',
    'Egypt': 'EGY',
    'England': 'ENG',
    'France': 'FRA',
    'Germany': 'GER',
    'Ghana': 'GHA',
    'Haiti': 'HAI',
    'Iran': 'IRN',
    'Iraq': 'IRQ',
    'Ivory Coast': 'CIV',
    'Japan': 'JPN',
    'Jordan': 'JOR',
    'Mexico': 'MEX',
    'Morocco': 'MAR',
    'Netherlands': 'NED',
    'New Zealand': 'NZL',
    'Norway': 'NOR',
    'Panama': 'PAN',
    'Paraguay': 'PAR',
    'Portugal': 'POR',
    'Qatar': 'QAT',
    'Saudi Arabia': 'KSA',
    'Scotland': 'SCO',
    'Senegal': 'SEN',
    'South Africa': 'RSA',
    'South Korea': 'KOR',
    'Spain': 'ESP',
    'Sweden': 'SWE',
    'Switzerland': 'SUI',
    'Tunisia': 'TUN',
    'Turkey': 'TUR',
    'United States': 'USA',
    'Uruguay': 'URU',
    'Uzbekistan': 'UZB',
}

CSV_GROUP_MATCHES = 'group_matches.csv'
CSV_PROBABILITIES = 'world_cup_probabilities.csv'
HTML_GROUP_TABLES = 'group_tables.html'
CSV_RESULTS = 'results.csv'
OUTPUT_HTML = 'world_cup_dashboard.html'


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", '-', value)
    return value.strip('-')


def flag_emoji(team_name: str) -> str:
    code = TEAM_FLAGS.get(team_name)
    if not code:
        return ''
    return ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in code)


def team_code(team_name: str) -> str:
    return TEAM_CODES.get(team_name, '')


def parse_score_cell(cell: str):
    if not isinstance(cell, str) or not cell.strip():
        return None
    score = cell.split(' (')[0].strip()
    match = re.search(r'\(([\d.]+)%\)', cell)
    prob = float(match.group(1)) if match else None
    return {'score': score, 'prob': prob}


def load_matches():
    results = load_match_results()
    df = pd.read_csv(CSV_GROUP_MATCHES)
    matches = []
    for _, row in df.iterrows():
        team_a, team_b = [t.strip() for t in row['match'].split('vs')]
        top_scores = [parse_score_cell(row.get(f'Top {i} score')) for i in range(1, 6)]
        top_scores = [score for score in top_scores if score]
        key = tuple(sorted([team_a, team_b]))
        result_info = results.get(key, {})
        matches.append({
            'teamA': team_a,
            'teamB': team_b,
            'slugA': slugify(team_a),
            'slugB': slugify(team_b),
            'flagA': flag_emoji(team_a),
            'flagB': flag_emoji(team_b),
            'codeA': team_code(team_a),
            'codeB': team_code(team_b),
            'pA': float(row['P(first win)'] or 0),
            'pDraw': float(row['P(draw)'] or 0),
            'pB': float(row['P(second win)'] or 0),
            'topScores': top_scores,
            'date': result_info.get('date', ''),
            'location': result_info.get('location', ''),
        })
    return matches


def load_probabilities():
    df = pd.read_csv(CSV_PROBABILITIES)
    teams = []
    for _, row in df.iterrows():
        name = str(row['Team']).strip()
        teams.append({
            'name': name,
            'slug': slugify(name),
            'flag': flag_emoji(name),
            'code': team_code(name),
            'qualifiedR32': float(row['Qualified for R32 %'] or 0),
            'qualifiedR16': float(row['Qualified for R16 %'] or 0),
            'qualifiedQF': float(row['Qualified for QF %'] or 0),
            'qualifiedSF': float(row['Qualified for SF %'] or 0),
            'qualifiedFinal': float(row['Qualified for Final %'] or 0),
            'winner': float(row['World Cup winner %'] or 0),
            'runnerUp': float(row['Runner up %'] or 0),
            'thirdPlace': float(row['Third place %'] or 0),
            'thirdOrFourth': float(row['3rd or 4th place %'] or 0),
        })
    return teams


def load_group_table_html():
    try:
        with open(HTML_GROUP_TABLES, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return ''


def load_match_results():
    df = pd.read_csv(CSV_RESULTS)
    results = {}
    for _, row in df.iterrows():
        home = str(row['Home Team']).strip()
        away = str(row['Away Team']).strip()
        key = tuple(sorted([home, away]))
        city = str(row.get('City ', '') or '').strip()
        country = str(row.get('Country', '') or '').strip()
        location = ', '.join([part for part in [city, country] if part])
        results[key] = {
            'date': str(row.get('Date', '') or '').strip(),
            'city': city,
            'country': country,
            'location': location,
        }
    return results


def build_page(matches, teams, group_table_html):
    data = {
        'matches': matches,
        'teams': teams,
    }
    data_json = json.dumps(data)
    group_html_json = json.dumps(group_table_html)

    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>World Cup Forecast Center</title>
  <meta name="description" content="Interactive World Cup probability dashboard with team chances, stage progression, and top scoreline predictions." />
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.plot.ly/plotly-2.34.0.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js"></script>
  <style>
    body { font-family: 'Inter', sans-serif; margin: 0; padding: 0; background: #0f172a; color: #e2e8f0; }
    a { color: #38bdf8; }
    .page { max-width: 1440px; margin: 0 auto; padding: 24px; }
    .hero { display: grid; gap: 16px; margin-bottom: 32px; padding: 32px 0 40px; text-align: center; }
    .hero h1 { margin: 0; font-size: clamp(2rem, 3vw, 3.5rem); line-height: 1.05; }
    .hero p { color: #94a3b8; margin: 0 auto; max-width: 760px; }
    .tabs { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 24px; justify-content: center; }
    .tab-button { border: none; border-radius: 9999px; padding: 12px 20px; cursor: pointer; background: #1e293b; color: #cbd5e1; font-weight: 600; }
    .tab-button.active { background: linear-gradient(135deg,#0ea5e9,#8b5cf6); color: #fff; }
    .panel { display: none; }
    .panel.active { display: block; }
    .card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
    .card { background: rgba(15, 23, 42, 0.92); border: 1px solid rgba(148, 163, 184, 0.12); border-radius: 18px; padding: 20px; box-shadow: 0 20px 60px rgba(15,23,42,.25); }
    .card h3 { margin: 0 0 12px; font-size: 0.95rem; color: #e2e8f0; }
    .card .metric { font-size: 2rem; font-weight: 800; color: #f8fafc; }
    .metric-small { color: #94a3b8; margin-top: 8px; }
    .chart-row { display: grid; gap: 18px; margin-bottom: 24px; }
    .chart-box { background: rgba(15, 23, 42, 0.92); border: 1px solid rgba(148, 163, 184, 0.12); border-radius: 20px; padding: 18px; }
    .table-panel { overflow-x: auto; margin-bottom: 24px; }
    table { width: 100%; border-collapse: collapse; }
    thead th { text-align: left; padding: 14px 16px; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; border-bottom: 1px solid rgba(148,163,184,.16); }
    tbody tr { transition: background 0.18s ease; }
    tbody tr:hover { background: rgba(148, 163, 184, 0.08); }
    td { padding: 14px 16px; border-bottom: 1px solid rgba(148,163,184,.08); vertical-align: middle; }
    .team-name { display: inline-flex; align-items: center; gap: 8px; font-weight: 600; }
    .bar-row { display: flex; gap: 4px; height: 16px; border-radius: 999px; overflow: hidden; background: #1e293b; }
    .bar-segment { height: 100%; }
    .bar-win { background: #22c55e; }
    .bar-draw { background: #facc15; }
    .bar-loss { background: #ef4444; }
    .mini-score { font-size: 0.88rem; color: #94a3b8; margin-top: 6px; }
    .stage-tabs { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }
    .stage-tab, .group-tab { border: 1px solid rgba(148,163,184,.24); border-radius: 999px; padding: 10px 18px; background: #1e293b; color: #cbd5e1; cursor: pointer; font-weight: 600; }
    .stage-tab.active, .group-tab.active { background: linear-gradient(135deg,#0ea5e9,#8b5cf6); color: #fff; border-color: transparent; }
    .group-tabs { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }
    .match-filter-row { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
    .match-filter-row label { color: #cbd5e1; font-weight: 600; }
    .group-match-heading { font-size: 1rem; margin-bottom: 12px; color: #e2e8f0; }
    .score-list { margin-top: 6px; display: grid; gap: 4px; color: #cbd5e1; font-size: 0.88rem; }
    .score-list div { padding: 4px 8px; background: rgba(148,163,184,.06); border-radius: 10px; }
    .team-selector { margin: 16px 0 28px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
    select { min-width: 260px; border-radius: 14px; border: 1px solid rgba(148,163,184,.20); padding: 14px 16px; background: #0f172a; color: #e2e8f0; font-size: 1rem; }
    .team-summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .match-card { background: rgba(15,23,42,.95); border: 1px solid rgba(148,163,184,.14); border-radius: 18px; padding: 18px; margin-bottom: 16px; }
    .match-card h4 { margin: 0 0 8px; font-size: 1rem; }
    .match-row { display: grid; grid-template-columns: repeat(2, minmax(140px, 1fr)); gap: 12px; align-items: center; margin-bottom: 12px; }
    .score-preview { font-size: 0.95rem; color: #cbd5e1; }
    .group-tables-section { margin-top: 24px; }
    .group-tables-section h3 { margin-bottom: 18px; }
    .raw-group-table { overflow-x: auto; }
    .raw-group-table table { margin-bottom: 18px; }
    .team-pill { display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 999px; background: rgba(30,41,59,.95); border: 1px solid rgba(148,163,184,.12); }
    .summary-card strong { display: block; font-size: 1.45rem; margin-top: 6px; color: #f8fafc; }
  </style>
</head>
<body>
  <div class="page">
    <div class="hero">
      <div>
        <h1>World Cup Prediction Dashboard</h1>
        <p>Interactive insight into every team’s stage probability, match odds, and the top five most likely scorelines for every game.</p>
      </div>
    </div>
    <div class="tabs">
      <button class="tab-button active" data-panel="overview">Overview</button>
      <button class="tab-button" data-panel="team-detail">Team Detail</button>
    </div>

    <div id="overview" class="panel active">
      <div class="card-grid">
        <div class="card"><h3>Top finalist probability</h3><div id="top-finalist" class="metric">–</div><div class="metric-small">Team with the highest chance to reach the final</div></div>
        <div class="card"><h3>Top winner probability</h3><div id="top-winner" class="metric">–</div><div class="metric-small">Team most likely to win the World Cup</div></div>
        <div class="card"><h3>Most likely semifinalists</h3><div id="top-sf" class="metric">–</div><div class="metric-small">Aggregated semifinal qualification strength</div></div>
      </div>

      <div class="chart-row">
        <div class="chart-box">
          <div class="stage-tabs" id="stage-tabs"></div>
          <div id="stage-chart" style="height:460px;"></div>
        </div>
      </div>

      <div class="table-panel">
        <h2>Predicted group match probabilities</h2>
        <div class="group-tabs" id="group-tabs"></div>
        <div id="match-table"></div>
      </div>

      <div class="group-tables-section">
        <h3>Most likely group tables</h3>
        <div class="raw-group-table" id="group-tables"></div>
      </div>
    </div>

    <div id="team-detail" class="panel">
      <div class="team-selector">
        <label for="team-select">Select a team:</label>
        <select id="team-select"></select>
      </div>
      <div class="team-summary" id="team-cards"></div>
      <div class="group-tables-section">
        <h3>Team's group table</h3>
        <div class="raw-group-table" id="team-group-table"></div>
      </div>
      <div class="chart-row">
        <div class="chart-box"><h3>Progression outlook</h3><div id="team-stage-chart" style="height:360px;"></div></div>
      </div>
      <div class="table-panel">
        <h2>Team match preview</h2>
        <div id="team-matches"></div>
      </div>
    </div>
  </div>

  <script>
    window.WORLD_CUP_DATA = {"data": {}};
    window.WORLD_CUP_DATA = {"data": {}};
    const dashboardData = {"data": {}};
  </script>
  <script>
    let RAW_DATA = __DATA_JSON__;
    let GROUP_TABLE_HTML = __GROUP_HTML_JSON__;
    let teams = RAW_DATA.teams;
    let matches = RAW_DATA.matches;

    function parseCSV(text) {
      return Papa.parse(text.trim(), { header: true, skipEmptyLines: true }).data;
    }

    function safeNumber(value) {
      const num = parseFloat((value || '').toString().replace('%', '').trim());
      return Number.isFinite(num) ? num : 0;
    }

    function slugify(value) {
      return (value || '').toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    }

    function flagEmoji(teamName) {
      const flags = { 'Algeria': 'DZ', 'Argentina': 'AR', 'Australia': 'AU', 'Austria': 'AT', 'Belgium': 'BE', 'Bosnia and Herzegovina': 'BA', 'Brazil': 'BR', 'Canada': 'CA', 'Cape Verde': 'CV', 'Colombia': 'CO', 'Croatia': 'HR', 'Curaçao': 'CW', 'Czech Republic': 'CZ', 'DR Congo': 'CD', 'Ecuador': 'EC', 'Egypt': 'EG', 'England': 'GB', 'France': 'FR', 'Germany': 'DE', 'Ghana': 'GH', 'Haiti': 'HT', 'Iran': 'IR', 'Iraq': 'IQ', 'Ivory Coast': 'CI', 'Japan': 'JP', 'Jordan': 'JO', 'Mexico': 'MX', 'Morocco': 'MA', 'Netherlands': 'NL', 'New Zealand': 'NZ', 'Norway': 'NO', 'Panama': 'PA', 'Paraguay': 'PY', 'Portugal': 'PT', 'Qatar': 'QA', 'Saudi Arabia': 'SA', 'Scotland': 'GB', 'Senegal': 'SN', 'South Africa': 'ZA', 'South Korea': 'KR', 'Spain': 'ES', 'Sweden': 'SE', 'Switzerland': 'CH', 'Tunisia': 'TN', 'Turkey': 'TR', 'United States': 'US', 'Uruguay': 'UY', 'Uzbekistan': 'UZ' };
      const code = flags[teamName];
      return code ? String.fromCharCode(0x1F1E6 + code.charCodeAt(0) - 65, 0x1F1E6 + code.charCodeAt(1) - 65) : '';
    }

    function teamCode(teamName) {
      const codes = { 'Algeria': 'ALG', 'Argentina': 'ARG', 'Australia': 'AUS', 'Austria': 'AUT', 'Belgium': 'BEL', 'Bosnia and Herzegovina': 'BIH', 'Brazil': 'BRA', 'Canada': 'CAN', 'Cape Verde': 'CPV', 'Colombia': 'COL', 'Croatia': 'CRO', 'Curaçao': 'CUW', 'Czech Republic': 'CZE', 'DR Congo': 'COD', 'Ecuador': 'ECU', 'Egypt': 'EGY', 'England': 'ENG', 'France': 'FRA', 'Germany': 'GER', 'Ghana': 'GHA', 'Haiti': 'HAI', 'Iran': 'IRN', 'Iraq': 'IRQ', 'Ivory Coast': 'CIV', 'Japan': 'JPN', 'Jordan': 'JOR', 'Mexico': 'MEX', 'Morocco': 'MAR', 'Netherlands': 'NED', 'New Zealand': 'NZL', 'Norway': 'NOR', 'Panama': 'PAN', 'Paraguay': 'PAR', 'Portugal': 'POR', 'Qatar': 'QAT', 'Saudi Arabia': 'KSA', 'Scotland': 'SCO', 'Senegal': 'SEN', 'South Africa': 'RSA', 'South Korea': 'KOR', 'Spain': 'ESP', 'Sweden': 'SWE', 'Switzerland': 'SUI', 'Tunisia': 'TUN', 'Turkey': 'TUR', 'United States': 'USA', 'Uruguay': 'URU', 'Uzbekistan': 'UZB' };
      return codes[teamName] || '';
    }

    function parseScoreCell(cell) {
      if (!cell) return null;
      const score = cell.split(' (')[0].trim();
      const match = cell.match(/\\(([^\\)]+)\\)/);
      const prob = match ? safeNumber(match[1]) : null;
      return score ? { score, prob } : null;
    }

function parseMatchPair(text) {
      const parts = text.split(' vs ');
      return { teamA: parts[0]?.trim() || '', teamB: parts[1]?.trim() || '' };
    }

    function loadTeamsFromCsv(rows) {
      return rows.map(row => ({
        name: row.Team?.trim() || '',
        slug: slugify(row.Team || ''),
        flag: flagEmoji(row.Team || ''),
        code: teamCode(row.Team || ''),
        qualifiedR32: safeNumber(row['Qualified for R32 %']),
        qualifiedR16: safeNumber(row['Qualified for R16 %']),
        qualifiedQF: safeNumber(row['Qualified for QF %']),
        qualifiedSF: safeNumber(row['Qualified for SF %']),
        qualifiedFinal: safeNumber(row['Qualified for Final %']),
        winner: safeNumber(row['World Cup winner %'])
      }));
    }

    function loadMatchesFromCsv(rows, results, teamMap) {
      const resultsByPair = new Map();
      results.forEach(row => {
        const home = row['Home Team']?.trim() || '';
        const away = row['Away Team']?.trim() || '';
        const key = `${home}|${away}`;
        resultsByPair.set(key, {
          date: row.Date?.trim() || '',
          location: [row['City ']?.trim(), row.Country?.trim()].filter(Boolean).join(', ')
        });
      });
      return rows.map(row => {
        const pair = parseMatchPair(row.match || '');
        const result = resultsByPair.get(`${pair.teamA}|${pair.teamB}`) || resultsByPair.get(`${pair.teamB}|${pair.teamA}`) || { date: '', location: '' };
        const teamAData = teamMap.get(pair.teamA) || { flag: '', code: '' };
        const teamBData = teamMap.get(pair.teamB) || { flag: '', code: '' };
        return {
          teamA: pair.teamA,
          teamB: pair.teamB,
          pA: safeNumber(row['P(first win)']),
          pDraw: safeNumber(row['P(draw)']),
          pB: safeNumber(row['P(second win)']),
          topScores: ['Top 1 score', 'Top 2 score', 'Top 3 score', 'Top 4 score', 'Top 5 score']
            .map(key => parseScoreCell(row[key]))
            .filter(Boolean),
          date: result.date,
          location: result.location,
          flagA: teamAData.flag,
          flagB: teamBData.flag,
          codeA: teamAData.code,
          codeB: teamBData.code
        };
      });
    }

    async function fetchText(url) {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Unable to fetch ${url}: ${response.status}`);
      }
      return response.text();
    }

    async function loadRemoteData() {
      try {
        const [matchesText, probText, resultsText, groupTablesText] = await Promise.all([
          fetchText('group_matches.csv'),
          fetchText('world_cup_probabilities.csv'),
          fetchText('results.csv'),
          fetchText('group_tables.html')
        ]);
        const teamRows = parseCSV(probText);
        const resultRows = parseCSV(resultsText);
        const matchRows = parseCSV(matchesText);
        const loadedTeams = loadTeamsFromCsv(teamRows);
        const teamMap = new Map(loadedTeams.map(team => [team.name, team]));
        const loadedMatches = loadMatchesFromCsv(matchRows, resultRows, teamMap);
        GROUP_TABLE_HTML = groupTablesText;
        return { teams: loadedTeams, matches: loadedMatches };
      } catch (error) {
        console.warn('Could not load CSV data, using embedded fallback data.', error);
        return { teams: RAW_DATA.teams, matches: RAW_DATA.matches };
      }
    }

    document.addEventListener('DOMContentLoaded', async () => {
      const loaded = await loadRemoteData();
      teams = loaded.teams;
      matches = loaded.matches;
      renderOverviewCards();
      renderStageCharts();
      renderGroupTabs();
      renderMatchTable();
      renderGroupTablePortion(selectedGroup);
      populateTeamSelector();
    });

    const panelButtons = document.querySelectorAll('.tab-button');
    panelButtons.forEach(button => {
      button.addEventListener('click', () => {
        panelButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        document.querySelectorAll('.panel').forEach(panel => panel.classList.remove('active'));
        document.getElementById(button.dataset.panel).classList.add('active');
      });
    });

    function formatTeamLabel(code, flag, name, compact = false) {
      return name.trim();
    }

    function renderOverviewCards() {
      const bestFinal = [...teams].sort((a,b)=>b.qualifiedFinal-a.qualifiedFinal)[0];
      const bestWinner = [...teams].sort((a,b)=>b.winner-a.winner)[0];
      const bestSF = [...teams].sort((a,b)=>b.qualifiedSF-a.qualifiedSF)[0];
      document.getElementById('top-finalist').textContent = `${formatTeamLabel(bestFinal.code, bestFinal.flag, bestFinal.name)} ${bestFinal.qualifiedFinal.toFixed(1)}%`;
      document.getElementById('top-winner').textContent = `${formatTeamLabel(bestWinner.code, bestWinner.flag, bestWinner.name)} ${bestWinner.winner.toFixed(1)}%`;
      document.getElementById('top-sf').textContent = `${formatTeamLabel(bestSF.code, bestSF.flag, bestSF.name)} ${bestSF.qualifiedSF.toFixed(1)}%`;
    }

    const STAGE_KEYS = {
      'R32': { key: 'qualifiedR32', label: 'Round of 32', color: '#38bdf8' },
      'R16': { key: 'qualifiedR16', label: 'Round of 16', color: '#8b5cf6' },
      'QF': { key: 'qualifiedQF', label: 'Quarterfinals', color: '#14b8a6' },
      'SF': { key: 'qualifiedSF', label: 'Semifinals', color: '#f97316' },
      'Final': { key: 'qualifiedFinal', label: 'Final', color: '#0ea5e9' },
      'Winner': { key: 'winner', label: 'World Cup winner', color: '#22c55e' }
    };
    let selectedStage = 'Final';

    function renderStageTabs() {
      const container = document.getElementById('stage-tabs');
      container.innerHTML = Object.keys(STAGE_KEYS).map(stage => ` <button class='stage-tab${stage === selectedStage ? ' active' : ''}' data-stage='${stage}'>${stage}</button>`).join('');
      container.querySelectorAll('.stage-tab').forEach(button => {
        button.addEventListener('click', () => {
          selectedStage = button.dataset.stage;
          renderStageTabs();
          renderStageChart();
        });
      });
    }

    function renderStageChart() {
      const sortedTeams = [...teams].sort((a,b)=>b.qualifiedFinal-a.qualifiedFinal);
      const names = sortedTeams.map(t=>t.name);
      const stage = STAGE_KEYS[selectedStage];
      const values = sortedTeams.map(t => t[stage.key]);
      Plotly.newPlot('stage-chart', [{ x: names, y: values, type: 'bar', marker: { color: stage.color } }], {
        margin:{t:40,r:20,l:60,b:160},
        plot_bgcolor:'#0f172a',
        paper_bgcolor:'#0f172a',
        font:{color:'#e2e8f0'},
        xaxis:{tickangle:-45,automargin:true},
        yaxis:{title:'Probability (%)'},
        title:{text:stage.label, font:{size:18}}
      });
    }

    function renderStageCharts() {
      renderStageTabs();
      renderStageChart();
    }

    const GROUPS = {
      'A': ["Mexico", "South Africa", "South Korea", "Czech Republic"],
      'B': ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
      'C': ["Brazil", "Morocco", "Haiti", "Scotland"],
      'D': ["United States", "Paraguay", "Australia", "Turkey"],
      'E': ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
      'F': ["Netherlands", "Japan", "Sweden", "Tunisia"],
      'G': ["Belgium", "Egypt", "Iran", "New Zealand"],
      'H': ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
      'I': ["France", "Senegal", "Iraq", "Norway"],
      'J': ["Argentina", "Algeria", "Austria", "Jordan"],
      'K': ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
      'L': ["England", "Croatia", "Ghana", "Panama"]
    };
    let selectedGroup = 'A';

    function renderGroupTabs() {
      const container = document.getElementById('group-tabs');
      container.innerHTML = Object.keys(GROUPS).map(group => ` <button class='group-tab${group === selectedGroup ? ' active' : ''}' data-group='${group}'>Group ${group}</button>`).join('');
      container.querySelectorAll('.group-tab').forEach(button => {
        button.addEventListener('click', () => {
          selectedGroup = button.dataset.group;
          renderGroupTabs();
          renderMatchTable();
          renderGroupTablePortion(selectedGroup);
        });
      });
    }

    function getGroupMatches(group) {
      const members = new Set(GROUPS[group] || []);
      return matches.filter(match => members.has(match.teamA) && members.has(match.teamB));
    }

    function renderMatchTable() {
      const container = document.getElementById('match-table');
      const filteredMatches = getGroupMatches(selectedGroup).slice().sort((a, b) => {
        if (!a.date || !b.date) return 0;
        return new Date(a.date) - new Date(b.date);
      });
      const rows = filteredMatches.map(match => {
        const topScores = match.topScores.slice(0,5).map(score => `<div>${score.score} (${score.prob.toFixed(1)}%)</div>`).join('');
        const locationLine = match.date || match.location ? `<div class='mini-score'>${match.date}${match.date && match.location ? ' · ' : ''}${match.location || ''}</div>` : '';
        const labelA = formatTeamLabel(match.codeA, match.flagA, match.teamA, true);
        const labelB = formatTeamLabel(match.codeB, match.flagB, match.teamB, true);
        return `<tr><td><span class='team-name'>${labelA}</span> vs <span class='team-name'>${labelB}</span>${locationLine}</td><td><div class='bar-row'><span class='bar-segment bar-win' style='width:${match.pA}%' title='${match.pA.toFixed(1)}%'></span><span class='bar-segment bar-draw' style='width:${match.pDraw}%' title='${match.pDraw.toFixed(1)}%'></span><span class='bar-segment bar-loss' style='width:${match.pB}%' title='${match.pB.toFixed(1)}%'></span></div><div class='mini-score'>${match.pA.toFixed(1)}% ${match.teamA} win · ${match.pDraw.toFixed(1)}% draw · ${match.pB.toFixed(1)}% ${match.teamB} win</div></td><td><div class='score-list'>${topScores}</div></td></tr>`;
      }).join('');
      if (!rows) {
        container.innerHTML = `<div class='match-card'><h4>No matches found for Group ${selectedGroup}</h4></div>`;
        return;
      }
      container.innerHTML = `<div class='group-match-heading'>Showing group ${selectedGroup} fixtures</div><table><thead><tr><th>Match</th><th>Outcome split</th><th>Top 5 predicted scores</th></tr></thead><tbody>${rows}</tbody></table>`;
    }

    function renderGroupTablePortion(group, containerId = 'group-tables') {
      const container = document.getElementById(containerId);
      const parser = new DOMParser();
      const doc = parser.parseFromString(GROUP_TABLE_HTML, 'text/html');
      const sourceTable = doc.querySelector('table');
      if (!sourceTable) {
        container.innerHTML = '';
        return;
      }
      const groupIndex = Object.keys(GROUPS).indexOf(group);
      if (groupIndex < 0) {
        container.innerHTML = '';
        return;
      }
      const start = 1 + groupIndex * 4;
      const end = start + 3;
      const portionTable = document.createElement('table');
      const sourceHead = sourceTable.tHead;
      if (sourceHead) {
        const newHead = portionTable.createTHead();
        Array.from(sourceHead.rows).forEach((row, rowIndex) => {
          if (rowIndex === 0) {
            return; // skip the top group label row
          }
          const newRow = row.cloneNode(false);
          Array.from(row.children).forEach((cell, idx) => {
            if (idx === 0 || (idx >= start && idx <= end)) {
              newRow.appendChild(cell.cloneNode(true));
            }
          });
          newHead.appendChild(newRow);
        });
      }
      const sourceBody = sourceTable.tBodies[0];
      const newBody = portionTable.createTBody();
      if (sourceBody) {
        Array.from(sourceBody.rows).forEach(row => {
          const newRow = row.cloneNode(false);
          Array.from(row.children).forEach((cell, idx) => {
            if (idx === 0 || (idx >= start && idx <= end)) {
              newRow.appendChild(cell.cloneNode(true));
            }
          });
          newBody.appendChild(newRow);
        });
      }
      container.innerHTML = `<div class='group-match-heading'>Group ${group} table</div>`;
      container.appendChild(portionTable);
    }

    function renderTeamGroupTables(teamName) {
      renderTeamGroupTable(teamName);
    }

    function populateTeamSelector() {
      const select = document.getElementById('team-select');
      select.innerHTML = teams.sort((a,b)=>a.name.localeCompare(b.name)).map(team => ` <option value='${team.slug}'>${team.name}</option>`).join('');
      select.addEventListener('change', () => renderTeamDetail(select.value));
      renderTeamDetail(select.value);
    }

    function renderTeamDetail(slug) {
      const team = teams.find(t => t.slug === slug) || teams[0];
      const cards = document.getElementById('team-cards');
      cards.innerHTML = `
        <div class='card summary-card'><h3>${team.name}</h3><strong>${team.qualifiedR32.toFixed(1)}%</strong><span>Round of 32</span></div>
        <div class='card summary-card'><h3>Round of 16</h3><strong>${team.qualifiedR16.toFixed(1)}%</strong><span>Round of 16</span></div>
        <div class='card summary-card'><h3>Quarterfinal</h3><strong>${team.qualifiedQF.toFixed(1)}%</strong><span>Quarterfinals</span></div>
        <div class='card summary-card'><h3>Semifinal</h3><strong>${team.qualifiedSF.toFixed(1)}%</strong><span>Semifinals</span></div>
        <div class='card summary-card'><h3>Final</h3><strong>${team.qualifiedFinal.toFixed(1)}%</strong><span>Final qualification</span></div>
        <div class='card summary-card'><h3>Champion</h3><strong>${team.winner.toFixed(1)}%</strong><span>World Cup winner</span></div>
      `;
      renderTeamGroupTable(team.name);
      Plotly.newPlot('team-stage-chart', [{ x:['R32','R16','QF','SF','Final','Winner'], y:[team.qualifiedR32,team.qualifiedR16,team.qualifiedQF,team.qualifiedSF,team.qualifiedFinal,team.winner], type:'bar', marker:{color:['#38bdf8','#8b5cf6','#22c55e','#f97316','#0ea5e9','#10b981']} }], { margin:{t:30,r:20,l:60,b:50}, plot_bgcolor:'#0f172a', paper_bgcolor:'#0f172a', font:{color:'#e2e8f0'}, yaxis:{title:'Probability (%)'} });
      renderTeamMatches(team.name);
    }

    function getTeamGroup(teamName) {
      return Object.entries(GROUPS).find(([group, teams]) => teams.includes(teamName))?.[0] || '';
    }

    function renderTeamGroupTable(teamName) {
      const group = getTeamGroup(teamName);
      if (group) {
        renderGroupTablePortion(group, 'team-group-table');
      } else {
        const container = document.getElementById('team-group-table');
        if (container) container.innerHTML = '';
      }
    }

    function renderTeamMatches(teamName) {
      const container = document.getElementById('team-matches');
      const teamMatches = matches.filter(match => match.teamA === teamName || match.teamB === teamName);
      container.innerHTML = teamMatches.map(match => {
        const opponent = match.teamA === teamName ? match.teamB : match.teamA;
        const ourProb = match.teamA === teamName ? match.pA : match.pB;
        const oppProb = match.teamA === teamName ? match.pB : match.pA;
        const drawProb = match.pDraw;
        const title = match.teamA === teamName ? `${formatTeamLabel(match.codeA, match.flagA, match.teamA, true)} vs ${formatTeamLabel(match.codeB, match.flagB, match.teamB, true)}` : `${formatTeamLabel(match.codeB, match.flagB, match.teamB, true)} vs ${formatTeamLabel(match.codeA, match.flagA, match.teamA, true)}`;
        const topScore = match.topScores.length ? `${match.topScores[0].score} (${match.topScores[0].prob.toFixed(1)}%)` : '—';
        const dateLine = match.date || match.location ? `<div class='mini-score'>${match.date}${match.date && match.location ? ' · ' : ''}${match.location || ''}</div>` : '';
        return `
          <div class='match-card'>
            <h4>${title}</h4>
            ${dateLine}
            <div class='match-row'><div><span class='team-name'>${formatTeamLabel(match.codeA, match.flagA, match.teamA)}</span></div><div class='score-preview'>${match.pA.toFixed(1)}%</div></div>
            <div class='match-row'><div><span class='team-name'>${formatTeamLabel(match.codeB, match.flagB, match.teamB)}</span></div><div class='score-preview'>${match.pB.toFixed(1)}%</div></div>
            <div class='bar-row'><span class='bar-segment bar-win' style='width:${ourProb}%'></span><span class='bar-segment bar-draw' style='width:${drawProb}%'></span><span class='bar-segment bar-loss' style='width:${oppProb}%'></span></div>
            <div class='mini-score'>Best scoreline: ${topScore}</div>
          </div>`;
      }).join('');
    }

    document.addEventListener('DOMContentLoaded', () => {
      renderOverviewCards();
      renderStageCharts();
      renderGroupTabs();
      renderMatchTable();
      renderGroupTablePortion(selectedGroup);
      populateTeamSelector();
    });
  </script>
</body>
</html>"""
    html_template = html_template.replace('__DATA_JSON__', data_json).replace('__GROUP_HTML_JSON__', group_html_json)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_template)


def main():
    matches = load_matches()
    teams = load_probabilities()
    group_table_html = load_group_table_html()
    build_page(matches, teams, group_table_html)
    print(f'Generated {OUTPUT_HTML} with {len(teams)} teams and {len(matches)} matches.')


if __name__ == '__main__':
    main()
