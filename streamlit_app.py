import streamlit as st
import google.generativeai as genai
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random
import traceback

# --- CSS・フォント・アニメーション設定 ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Roboto+Mono&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&display=swap" rel="stylesheet">
<style>
.stApp {
    background: linear-gradient(135deg, #c9f0ff 0%, #f0f9ff 100%);
    font-family: 'Roboto Mono', monospace;
    color: #003366;
    padding: 20px 40px;
}
/* タイトル用スタイル（色を濃い青に、サイズは控えめに） */
h1, .stTitle {
    font-family: 'Orbitron', 'Roboto Mono', monospace;
    font-weight: 900;
    font-size: 2.5rem !important;
    color: #003366;  /* 元の色 */
    text-shadow: 1.5px 1.5px 3px rgba(0, 51, 102, 0.5);
    margin-bottom: 20px;
    line-height: 1.2;
}
.css-1d391kg {
    background: #e0f7fa;
    padding: 20px;
    border-radius: 15px;
    font-weight: 600;
    font-size: 1.1rem;
}
div[data-testid="stChatMessage"][data-user="user"] {
    background-color: #a0d8ef;
    border-radius: 20px 20px 0 20px;
    padding: 15px;
    margin: 12px 0;
    color: #004466;
    font-weight: 600;
    font-size: 1rem;
}
div[data-testid="stChatMessage"][data-user="assistant"] {
    background-color: #ffdcf9;
    border-radius: 20px 20px 20px 0;
    padding: 15px;
    margin: 12px 0;
    color: #6a006a;
    font-weight: 600;
    font-size: 1rem;
    position: relative;
    overflow: hidden;
}
button[kind="primary"] {
    background-color: #ff77ff !important;
    color: white !important;
    font-weight: bold;
    border-radius: 12px;
    padding: 12px 25px;
    font-size: 1.1rem;
    transition: background-color 0.3s ease;
}
button[kind="primary"]:hover {
    background-color: #ff33cc !important;
    cursor: pointer;
}
@keyframes fadeIn {
    from {opacity: 0; transform: translateY(15px);}
    to {opacity: 1; transform: translateY(0);}
}
.fade-in {
    animation: fadeIn 0.8s ease forwards;
}
a {
    color: #cc00cc;
    font-weight: bold;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 style="
    font-family: 'Orbitron', 'Roboto Mono', monospace;
    font-weight: 900;
    font-size: 2.5rem;
    color: #003366;
    text-shadow: 1.5px 1.5px 3px rgba(0, 51, 102, 0.5);
    line-height: 1.2;
    margin-bottom: 20px;
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
">
  <span style="flex-shrink: 0;">🎧</span>
  <span style="display: flex; flex-direction: column; line-height: 1.3;">
    <span>どんな気分？</span>
    <span>ボカロ曲で教えてチャットボット</span>
  </span>
</h1>
""", unsafe_allow_html=True)


# APIキー設定
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
SPOTIFY_CLIENT_ID = st.secrets["SPOTIFY_CLIENT_ID"]
SPOTIFY_CLIENT_SECRET = st.secrets["SPOTIFY_CLIENT_SECRET"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-lite')

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

# セッションステート初期化
if "messages" not in st.session_state:
    st.session_state.messages = []

# メッセージ表示関数
def display_message(role, content):
    with st.chat_message(role):
        st.markdown(f'<div class="fade-in">{content}</div>', unsafe_allow_html=True)

# --- サイドバーUI ---
with st.sidebar:
    st.header("🎯 条件を選んで曲を探す")

    mood = st.selectbox(
        "今の気分は？",
        ["楽しい", "切ない", "かっこいい", "癒されたい", "落ち着きたい",
         "元気が欲しい", "感動したい", "ノスタルジックな気分", "盛り上がりたい",
         "しっとりしたい", "ワクワクしたい", "リラックスしたい", "考えたい", "その他"]
    )
    genre = st.multiselect(
        "ジャンルを選んでください",
        ["ポップ", "ロック", "エレクトロ", "バラード", "アップテンポ",
         "アコースティック", "クラシック", "その他"]
    )
    vocaloid = st.multiselect(
        "好きなボーカロイドは？",
        ["初音ミク", "鏡音リン", "鏡音レン", "巡音ルカ", "GUMI", "IA", "KAITO", "MEIKO", "その他"]
    )
    tempo_level = st.selectbox("曲の速さは？", ["速い", "普通", "遅い"])

    st.subheader("優先度を選ぶ（どの条件を重視するか）")
    options = ["気分", "ジャンル", "ボーカロイド", "速さ"]

    def select_priority(key, exclude=[]):
        choices = [o for o in options if o not in exclude]
        return st.selectbox(f"{key}の優先条件", choices, key=key)

    prio1 = select_priority("prio1")
    prio2 = select_priority("prio2", exclude=[prio1])
    prio3 = select_priority("prio3", exclude=[prio1, prio2])
    prio4 = [o for o in options if o not in [prio1, prio2, prio3]][0]

# チャット履歴を表示
for msg in st.session_state.messages:
    display_message(msg["role"], msg["content"])

# ユーザー自由入力
user_input = st.chat_input("気分や好きなボカロ曲の特徴を教えてください…")

# 優先度に従って検索クエリを組み立てる関数
def build_query_by_priority(priorities, mood, genre, vocaloid, tempo_level):
    parts = []
    for p in priorities:
        if p == "気分" and mood:
            parts.append(mood)
        elif p == "ジャンル" and genre:
            parts.extend(genre)
        elif p == "ボーカロイド":
            parts.extend(vocaloid if vocaloid else ["ボカロ"])
        elif p == "速さ":
            if tempo_level == "速い":
                parts.append("140-200 BPM")
            elif tempo_level == "普通":
                parts.append("100-139 BPM")
            else:
                parts.append("60-99 BPM")
    return " ".join(parts)

# Spotify検索＆Gemini AIでボカロ判定＆紹介（上位10曲からランダム1曲表示）
def search_and_recommend(query):
    with st.spinner('検索中です。少々お待ちください…'):
        try:
            results = sp.search(q=query + " ボカロ", type='track', limit=10)
            vocaloid_tracks = []

            for track in results.get('tracks', {}).get('items', []):
                track_name = track.get('name', '')
                artists = track.get('artists', [])
                artist_name = artists[0].get('name', '不明なアーティスト') if artists else '不明なアーティスト'

                if not track_name or not artist_name:
                    continue

                check_prompt = (
                    f"以下の楽曲はボカロ曲ですか？「はい」または「いいえ」で答えてください。\n"
                    f"曲名: {track_name}\nアーティスト: {artist_name}"
                )
                check_response = model.generate_content(check_prompt)
                is_vocaloid = check_response.text.strip().lower()

                if "はい" in is_vocaloid:
                    vocaloid_tracks.append(track)

            if not vocaloid_tracks:
                no_result_msg = "申し訳ありません。ボカロ曲が見つかりませんでした。別の条件でお試しください。"
                display_message("assistant", no_result_msg)
                st.session_state.messages.append({"role": "assistant", "content": no_result_msg})
                return

            track = random.choice(vocaloid_tracks)
            track_name = track.get('name', '曲名不明')
            artists = track.get('artists', [])
            artist_name = artists[0].get('name', '不明なアーティスト') if artists else '不明なアーティスト'
            track_url = track.get('external_urls', {}).get('spotify', '#')

            album_images = track.get('album', {}).get('images', [])
            album_img = album_images[0]['url'] if album_images else ""

            intro_prompt = (
                f"以下の曲の紹介文を100文字以内で書いてください。\n"
                f"曲名: {track_name}\nアーティスト: {artist_name}"
            )
            response = model.generate_content(intro_prompt)
            description = response.text.strip() or "紹介文はありませんでした。"

            assistant_message = (
                f'<div style="text-align:center">'
                f'{f"<img src=\"{album_img}\" width=\"300\" style=\"border-radius:15px; margin-bottom:10px;\" />" if album_img else ""}'
                f'</div>'
                f'<b>おすすめの曲は <span style="color:#cc00cc">{track_name}</span></b> / {artist_name} です。<br><br>'
                f'{description}<br><br>'
                f'<a href="{track_url}" target="_blank">▶ Spotifyで聴く</a>'
            )

            display_message("assistant", assistant_message)
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})

        except Exception as e:
            import traceback
            st.error("内部エラーが発生しました。しばらくしてから再度お試しください。")
            print(traceback.format_exc())
            err_msg = f"エラーが発生しました: {e}"
            display_message("assistant", err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})




# 選択肢から曲を推薦ボタン
if st.sidebar.button("🎵 選択肢から曲を推薦"):
    if not mood:
        st.sidebar.warning("気分を選んでください。")
    else:
        priorities = [prio1, prio2, prio3, prio4]
        query = build_query_by_priority(priorities, mood, genre, vocaloid, tempo_level)

        user_msg = f"選択肢で指定: {query}"
        st.session_state.messages.append({"role": "user", "content": user_msg})
        display_message("user", user_msg)

        search_and_recommend(query)

# 自由入力されたらSpotify検索して紹介
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    display_message("user", user_input)

    search_and_recommend(user_input)
