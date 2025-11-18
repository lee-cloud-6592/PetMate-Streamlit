import os
import json
import uuid
import hashlib
from datetime import datetime, date, time, timedelta
from dateutil import tz

import pandas as pd
import streamlit as st
# from cookies_manager import CookieManager # ❌ 쿠키 라이브러리 임포트 제거

# ===================== 기본 설정 =====================
st.set_page_config(page_title="PetMate", page_icon="🐾", layout="wide")

DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.json")
PET_FILE = os.path.join(DATA_DIR, "pets.json")
FEED_FILE = os.path.join(DATA_DIR, "feed_log.csv")
WATER_FILE = os.path.join(DATA_DIR, "water_log.csv")
MED_FILE = os.path.join(DATA_DIR, "med_schedule.json")
MED_LOG_FILE = os.path.join(DATA_DIR, "med_log.json")
HOSP_FILE = os.path.join(DATA_DIR, "hospital_events.json")
UNSAFE_FILE = os.path.join(DATA_DIR, "unsafe_db.json")

os.makedirs(DATA_DIR, exist_ok=True)


# ===================== 유틸 함수 =====================
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_csv(path, cols):
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            if set(df.columns) != set(cols):
                return pd.DataFrame(columns=cols)
            return df
        except:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)


def save_csv(path, df):
    df.to_csv(path, index=False)


def local_today():
    return datetime.now(tz.gettz("Asia/Seoul")).date()


def local_now():
    return datetime.now(tz.gettz("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")


def hash_password(pw: str):
    return hashlib.sha256(pw.encode()).hexdigest()

# 관리자 역할 확인 함수
def is_admin(username: str):
    """지정된 사용자가 관리자인지 확인 (아이디가 'admin'인 경우만)"""
    return username == "admin"


# ===================== 쿠키 기반 자동로그인 (기능 제거) =====================
# ❌ 쿠키 관리자 관련 로직 제거

def set_cookie(username):
    st.session_state.user = username

def clear_cookie():
    st.session_state.user = None


# ===================== 세션 초기화 =====================
if "user" not in st.session_state:
    st.session_state.user = None

# ❌ 쿠키 로드/복구 로직 제거


# ===================== 데이터 로딩 =====================
if "pets" not in st.session_state:
    st.session_state.pets = load_json(PET_FILE, [])

if "med_schedule" not in st.session_state:
    st.session_state.med_schedule = load_json(MED_FILE, [])

if "hospital_events" not in st.session_state:
    st.session_state.hospital_events = load_json(HOSP_FILE, [])

if "med_log" not in st.session_state:
    st.session_state.med_log = load_json(MED_LOG_FILE, {})

if "unsafe_db" not in st.session_state:
    default_unsafe = [
        {"category": "음식", "name": "초콜릿", "risk": "고위험", "why": "카카오 테오브로민 독성"},
        {"category": "음식", "name": "포도", "risk": "고위험", "why": "급성 신장손상"},
        {"category": "식물", "name": "스파티필름", "risk": "주의", "why": "독성 수산칼슘"},
    ]
    st.session_state.unsafe_db = load_json(UNSAFE_FILE, default_unsafe)

feed_cols = ["log_id", "pet_id", "date", "amount_g", "memo"]
water_cols = ["log_id", "pet_id", "date", "amount_ml", "memo"]

if "feed_df" not in st.session_state:
    st.session_state.feed_df = load_csv(FEED_FILE, feed_cols)
if "water_df" not in st.session_state:
    st.session_state.water_df = load_csv(WATER_FILE, water_cols)


# ===================== 로그인 화면 =====================
# ❌ 쿠키 로드 함수 호출 제거

def login_page():
    st.title("🐾 PetMate 로그인")
    st.info("로그인하면 모든 기능을 이용할 수 있어요!")

    users = load_json(USER_FILE, [])

    tab_login, tab_signup = st.tabs(["로그인", "회원가입"])

    # -------- 로그인 --------
    with tab_login:
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            hashed = hash_password(password)
            if any(u["username"] == username and u["password"] == hashed for u in users):
                set_cookie(username)
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    # -------- 회원가입 --------
    with tab_signup:
        new_user = st.text_input("새 아이디")
        new_pass = st.text_input("새 비밀번호", type="password")
        if st.button("회원가입"):
            if not new_user or not new_pass:
                st.error("아이디/비밀번호를 입력하세요.")
            elif any(u["username"] == new_user for u in users):
                st.error("이미 존재하는 아이디입니다.")
            else:
                users.append({"username": new_user, "password": hash_password(new_pass)})
                save_json(USER_FILE, users)
                st.success("회원가입 완료! 로그인해주세요.")

    st.stop()


# 로그인 체크 후 페이지 진행
if st.session_state.user is None:
    login_page()

# 로그인된 상태 상단 바
col_user, col_logout = st.columns([6, 1])
with col_user:
    st.write(f"👋 **{st.session_state.user}님 환영합니다!**")
with col_logout:
    if st.button("로그아웃"):
        clear_cookie()
        st.rerun()


# ===================== 메뉴 =====================
st.sidebar.title("🐾 PetMate")

# 💡 메뉴 옵션을 동적으로 구성
menu_options = [
    "대시보드",
    "반려동물 프로필",
    "사료/급수 기록",
    "복약 알림",
    "병원 일정",
    "위험 정보 검색",
]

# 관리자에게만 관리자 대시보드 메뉴 표시
if st.session_state.user and is_admin(st.session_state.user):
    menu_options.append("관리자 대시보드")
    
menu_options.append("데이터 관리")

page = st.sidebar.radio(
    "이동하기",
    tuple(menu_options),
)
# ========================= 권장량 계산 =========================
def recommended_food_grams(species: str, weight_kg: float):
    if weight_kg <= 0:
        return (0, 0)

    if species.lower() in ["개", "강아지", "dog"]:
        kcal = weight_kg * 30 + 70
        grams = round(kcal / 3.5)
    else:
        kcal = 60 * weight_kg
        grams = round(kcal / 3.5)

    snack_limit = round(grams * 0.1)
    return grams, snack_limit


def recommended_water_ml(weight_kg: float):
    return int(weight_kg * 60) if weight_kg > 0 else 0


# ========================= 공통 반려동물 선택 위젯 =========================
def pet_selector(label="반려동물 선택"):
    pets = [p for p in st.session_state.pets if p.get("name")]
    if not pets:
        st.info("먼저 '반려동물 프로필'에서 등록하세요!")
        return None
    options = {f"{p['name']} ({p['species']})": p for p in pets}
    # st.selectbox에는 key 인수가 필수이므로 유지
    choice = st.selectbox(label, list(options.keys()), key=f"pet_select_{page}") 
    return options[choice]


# ========================= 1) 대시보드 =========================
if page == "대시보드":
    st.header("📊 오늘 한눈에 보기")

    pet = pet_selector()
    if pet:
        col1, col2, col3 = st.columns(3) 

        # ------ 기본 정보 ------
        with col1:
            st.subheader("기본 정보")
            st.write(f"**이름:** {pet['name']}")
            st.write(f"**종:** {pet['species']}")
            st.write(f"**체중:** {pet.get('weight_kg', '-')} kg")
            if pet.get("birth"):
                st.write(f"**생일:** {pet['birth']}")
            if pet.get("notes"):
                st.caption(pet["notes"])

        # ------ 사료/간식 ------
        with col2:
            st.subheader("사료/간식")
            grams, snack_limit = recommended_food_grams(
                pet["species"], float(pet.get("weight_kg", 0))
            )
            today = local_today().isoformat()
            eaten = st.session_state.feed_df[
                (st.session_state.feed_df["pet_id"] == pet["id"])
                & (st.session_state.feed_df["date"] == today)
            ]["amount_g"].sum()

            st.write(f"권장량: **{grams} g** / 간식 상한: **{snack_limit} g**")
            # 권장량 계산 수식 표시
            if pet["species"].lower() in ["개", "강아지", "dog"]:
                st.latex(r"""
                \text{RER(kcal)} = (30 \times \text{체중(kg)}) + 70 \\
                \text{권장량(g)} \approx \text{RER} / 3.5
                """)
            else:
                st.latex(r"""
                \text{RER(kcal)} = 60 \times \text{체중(kg)} \\
                \text{권장량(g)} \approx \text{RER} / 3.5
                """)
            st.progress(min(1.0, eaten / grams if grams else 0), text=f"{int(eaten)} g")

        # ------ 물 급수 ------
        with col3:
            st.subheader("물 급수")
            wml = recommended_water_ml(float(pet.get("weight_kg", 0)))
            drank = st.session_state.water_df[
                (st.session_state.water_df["pet_id"] == pet["id"])
                & (st.session_state.water_df["date"] == today)
            ]["amount_ml"].sum()

            st.write(f"권장량: **{wml} ml**")
            # 권장량 계산 수식 표시
            st.latex(r"""
            \text{권장 급수량(ml)} \approx \text{체중(kg)} \times 60
            """)
            st.progress(min(1.0, drank / wml if wml else 0), text=f"{int(drank)} ml")


        # ------ 오늘 스케줄 ------
        st.divider()
        st.subheader("🕒 오늘 복약 / 병원 일정")

        # 복약
        today_str = local_today().isoformat()
        
        # pet_id와 date를 조합한 키로 복약 기록 가져오기
        today_med_log_key = f"{pet['id']}_{today_str}"
        today_med_logs = st.session_state.med_log.get(today_med_log_key, {})
        
        meds_today = []
        for m in st.session_state.med_schedule:
            if m["pet_id"] != pet["id"]:
                continue

            start_ok = not m.get("start") or m["start"] <= today_str
            end_ok = not m.get("end") or today_str <= m["end"]

            if start_ok and end_ok:
                for t in m.get("times", []):
                    med_id = m["id"]
                    log_key = f"{med_id}_{t}"
                    is_taken = log_key in today_med_logs
                    meds_today.append({
                        "id": med_id,
                        "시간": t,
                        "약": m["drug"],
                        "용량": f"{m['dose']}{m['unit']}",
                        "복용여부": "✅ 완료" if is_taken else "❌ 미완료"
                    })

        if meds_today:
            st.write("📌 복약 예정")
            df_med = pd.DataFrame(meds_today)[["시간", "약", "용량", "복용여부"]]
            st.table(df_med.sort_values("시간"))
        else:
            st.write("오늘 복약 일정 없음")

        # 병원 일정
        events = [
            e for e in st.session_state.hospital_events
            if e["pet_id"] == pet["id"] and e["dt"].startswith(today_str)
        ]

        if events:
            st.write("📌 병원 방문")
            df = pd.DataFrame(events)[["dt", "title", "place", "notes"]]
            df = df.rename(columns={"dt": "일시", "title": "제목", "place": "장소", "notes": "메모"})
            st.table(df)
        else:
            st.write("오늘 병원 일정 없음")


# ========================= 2) 반려동물 프로필 =========================
elif page == "반려동물 프로필":
    st.header("🐶 반려동물 프로필")

    st.subheader("반려동물 등록")
    with st.form("pet_form", clear_on_submit=True):
        name = st.text_input("이름*")
        species = st.selectbox("종류*", ["개", "고양이", "기타"])
        breed = st.text_input("품종")
        birth = st.date_input("생일", value=None)
        weight = st.number_input("체중(kg)", min_value=0.0, step=0.1)
        notes = st.text_area("메모")

        ok = st.form_submit_button("등록")

        if ok:
            if not name.strip():
                st.error("이름은 필수입니다.")
            else:
                new_pet = {
                    "id": str(uuid.uuid4()),
                    "name": name.strip(),
                    "species": species,
                    "breed": breed.strip(),
                    "birth": birth.isoformat() if birth else "",
                    "weight_kg": float(weight),
                    "notes": notes.strip()
                }
                st.session_state.pets.append(new_pet)
                save_json(PET_FILE, st.session_state.pets)
                st.success(f"{name} 등록 완료!")
                st.rerun()

    # ---------------------- 목록/편집 ----------------------
    st.subheader("등록된 반려동물")
    if not st.session_state.pets:
        st.info("아직 등록된 반려동물이 없습니다.")
    else:
        for p in st.session_state.pets:
            with st.expander(f"{p['name']} ({p['species']})"):
                colA, colB = st.columns([2, 1])
                with colA:
                    p["name"] = st.text_input("이름", p["name"], key=f"name_{p['id']}")
                    p["species"] = st.selectbox("종류", ["개", "고양이", "기타"],
                                                 index=["개","고양이","기타"].index(p["species"]),
                                                 key=f"species_{p['id']}")
                    p["breed"] = st.text_input("품종", p["breed"], key=f"breed_{p['id']}")
                    p["birth"] = st.text_input("생일(YYYY-MM-DD)", p["birth"], key=f"birth_{p['id']}")
                    p["weight_kg"] = st.number_input("체중(kg)", value=float(p.get("weight_kg", 0)),
                                                     step=0.1, key=f"weight_{p['id']}")
                    p["notes"] = st.text_area("메모", value=p.get("notes", ""), key=f"notes_{p['id']}")

                with colB:
                    if st.button("저장", key=f"save_{p['id']}"):
                        save_json(PET_FILE, st.session_state.pets)
                        st.success("저장 완료!")
                        st.rerun()

                    if st.button("삭제", key=f"delete_{p['id']}"):
                        st.session_state.pets = [x for x in st.session_state.pets if x["id"] != p["id"]]
                        save_json(PET_FILE, st.session_state.pets)
                        st.warning("삭제되었습니다.")
                        st.rerun()


# ========================= 3) 사료 / 급수 기록 =========================
elif page == "사료/급수 기록":
    st.header("🍽️ 사료 / 급수 기록")

    pet = pet_selector()
    if pet:

        # -------- 기록 추가 (날짜 지정 가능) --------
        st.subheader("기록 추가")
        with st.form("feed_water_form", clear_on_submit=True):
            
            # 💡 날짜 입력 위젯 추가: 기본값은 오늘 날짜
            log_date = st.date_input("날짜 지정", value=local_today())
            
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                food_g = st.number_input("사료 / 간식 (g)", min_value=0, step=5)
                food_memo = st.text_input("사료 메모")

            with col2:
                water_ml = st.number_input("급수량 (ml)", min_value=0, step=10)
                water_memo = st.text_input("물 메모")

            ok = st.form_submit_button("저장하기")

            if ok:
                # 💡 지정된 날짜를 isoformat으로 사용
                selected_date_iso = log_date.isoformat()

                # 사료 추가
                if food_g > 0:
                    new_food = pd.DataFrame({
                        "log_id": [str(uuid.uuid4())],
                        "pet_id": [pet["id"]],
                        "date": [selected_date_iso], # 💡 지정된 날짜 사용
                        "amount_g": [int(food_g)],
                        "memo": [food_memo.strip()],
                    })
                    st.session_state.feed_df = pd.concat([st.session_state.feed_df, new_food], ignore_index=True)
                    save_csv(FEED_FILE, st.session_state.feed_df)

                # 물 추가
                if water_ml > 0:
                    new_water = pd.DataFrame({
                        "log_id": [str(uuid.uuid4())],
                        "pet_id": [pet["id"]],
                        "date": [selected_date_iso], # 💡 지정된 날짜 사용
                        "amount_ml": [int(water_ml)],
                        "memo": [water_memo.strip()],
                    })
                    st.session_state.water_df = pd.concat([st.session_state.water_df, new_water], ignore_index=True)
                    save_csv(WATER_FILE, st.session_state.water_df)

                st.success(f"[{log_date}] 날짜의 기록이 저장되었습니다!")
                st.rerun()

        # -------- 오늘 요약 --------
        st.subheader("오늘 요약")
        grams, snack_limit = recommended_food_grams(
            pet["species"],
            float(pet.get("weight_kg", 0)),
        )
        wml = recommended_water_ml(float(pet.get("weight_kg", 0)))
        today = local_today().isoformat()
        
        eaten = st.session_state.feed_df[(st.session_state.feed_df["pet_id"] == pet["id"]) & (st.session_state.feed_df["date"] == today)]["amount_g"].sum()
        drank = st.session_state.water_df[(st.session_state.water_df["pet_id"] == pet["id"]) & (st.session_state.water_df["date"] == today)]["amount_ml"].sum()

        colA, colB = st.columns(2)
        with colA:
            st.metric("사료/간식 섭취량", f"{int(eaten)} g", help=f"권장: {grams} g / 간식 상한: {snack_limit} g")
        with colB:
            st.metric("급수량", f"{int(drank)} ml", help=f"권장: {wml} ml")

        # -------- 기간별 조회 --------
        st.subheader("기록 조회")
        d1, d2 = st.columns(2)
        with d1:
            start = st.date_input("시작일", value=local_today() - timedelta(days=7), key="feed_start_date")
        with d2:
            end = st.date_input("종료일", value=local_today(), key="feed_end_date")

        mask_food = (
            (st.session_state.feed_df["pet_id"] == pet["id"]) &
            (st.session_state.feed_df["date"] >= start.isoformat()) &
            (st.session_state.feed_df["date"] <= end.isoformat())
        )
        mask_water = (
            (st.session_state.water_df["pet_id"] == pet["id"]) &
            (st.session_state.water_df["date"] >= start.isoformat()) &
            (st.session_state.water_df["date"] <= end.isoformat())
        )
        
        # 사료/간식 기록 및 삭제 기능
        st.write("🍖 사료/간식 기록")
        food_view_df = st.session_state.feed_df.loc[mask_food, ["log_id", "date", "amount_g", "memo"]].sort_values("date", ascending=False)
        food_view_df = food_view_df.rename(columns={"date": "날짜", "amount_g": "양(g)", "memo": "메모"})
        
        if not food_view_df.empty:
            # 💡 차트 데이터 준비 및 표시
            food_chart_df = food_view_df.groupby('날짜')['양(g)'].sum().reset_index()
            food_chart_df = food_chart_df.set_index('날짜')
            st.line_chart(food_chart_df, use_container_width=True) # ⬅️ 사료 섭취량 차트 표시

            for index, row in food_view_df.iterrows():
                col_food_data, col_food_del = st.columns([6, 1])
                with col_food_data:
                    st.text(f"[{row['날짜']}] {row['양(g)']}g ({row['메모']})")
                with col_food_del:
                    if st.button("삭제", key=f"del_food_{row['log_id']}"):
                        st.session_state.feed_df = st.session_state.feed_df[st.session_state.feed_df["log_id"] != row["log_id"]]
                        save_csv(FEED_FILE, st.session_state.feed_df)
                        st.warning("사료 기록 삭제 완료!")
                        st.rerun()
        else:
            st.info("기록 없음")
            
        st.divider()

        # 급수 기록 및 삭제 기능
        st.write("💧 급수 기록")
        water_view_df = st.session_state.water_df.loc[mask_water, ["log_id", "date", "amount_ml", "memo"]].sort_values("date", ascending=False)
        water_view_df = water_view_df.rename(columns={"date": "날짜", "amount_ml": "양(ml)", "memo": "메모"})

        if not water_view_df.empty:
            # 💡 차트 데이터 준비 및 표시
            water_chart_df = water_view_df.groupby('날짜')['양(ml)'].sum().reset_index()
            water_chart_df = water_chart_df.set_index('날짜')
            st.line_chart(water_chart_df, use_container_width=True) # ⬅️ 급수량 차트 표시
            
            for index, row in water_view_df.iterrows():
                col_water_data, col_water_del = st.columns([6, 1])
                with col_water_data:
                    st.text(f"[{row['날짜']}] {row['양(ml)']}ml ({row['메모']})")
                with col_water_del:
                    if st.button("삭제", key=f"del_water_{row['log_id']}"):
                        st.session_state.water_df = st.session_state.water_df[st.session_state.water_df["log_id"] != row["log_id"]]
                        save_csv(WATER_FILE, st.session_state.water_df)
                        st.warning("급수 기록 삭제 완료!")
                        st.rerun()
        else:
            st.info("기록 없음")


# ========================= 4) 복약 알림 =========================
elif page == "복약 알림":
    st.header("💊 복약 스케줄 관리")

    pet = pet_selector()
    if pet:
        today_str = local_today().isoformat()
        log_key_date = f"{pet['id']}_{today_str}"
        
        # 오늘 복약 기록 로드. 없으면 빈 딕셔너리
        today_med_logs = st.session_state.med_log.get(log_key_date, {})

        def update_med_log(med_id, time_str, is_taken):
            # 복약 상태 업데이트 함수
            log_key_med_time = f"{med_id}_{time_str}"
            if log_key_date not in st.session_state.med_log:
                st.session_state.med_log[log_key_date] = {}
            
            if is_taken:
                st.session_state.med_log[log_key_date][log_key_med_time] = local_now()
            elif log_key_med_time in st.session_state.med_log[log_key_date]:
                del st.session_state.med_log[log_key_date][log_key_med_time]
            
            save_json(MED_LOG_FILE, st.session_state.med_log)
            st.rerun()

        # -------- 오늘 복약 체크 --------
        st.subheader("🔔 오늘 복약 확인")
        meds = [m for m in st.session_state.med_schedule if m["pet_id"] == pet["id"]]
        meds_today_list = []
        for m in meds:
            start_ok = not m.get("start") or m["start"] <= today_str
            end_ok = not m.get("end") or today_str <= m["end"]
            
            if start_ok and end_ok:
                for t in sorted(m.get("times", [])):
                    med_time_key = f"{m['id']}_{t}"
                    is_taken = med_time_key in today_med_logs
                    
                    meds_today_list.append({
                        "id": m['id'],
                        "time": t,
                        "drug": m['drug'],
                        "dose": m['dose'],
                        "unit": m['unit'],
                        "is_taken": is_taken
                    })
        
        if meds_today_list:
            for item in meds_today_list:
                col_time, col_drug, col_check = st.columns([1, 4, 1]) 
                
                with col_time:
                    st.markdown(f"**{item['time']}**")
                
                with col_drug:
                    st.write(f"{item['drug']} ({item['dose']}{item['unit']})")

                with col_check:
                    # 체크박스 변경 시 update_med_log 함수 호출
                    if st.checkbox("복용 완료", value=item['is_taken'], 
                                   key=f"med_check_{item['id']}_{item['time']}"):
                        if not item['is_taken']:
                            update_med_log(item['id'], item['time'], True)
                    elif item['is_taken']:
                        update_med_log(item['id'], item['time'], False)
        else:
            st.info("오늘 복약 일정이 없습니다.")

        st.divider()

        # -------- 새 스케줄 추가 --------
        st.subheader("새 복약 스케줄 추가")
        with st.form("med_form", clear_on_submit=True):
            drug = st.text_input("약 이름*")
            dose = st.text_input("용량")
            unit = st.text_input("단위(정, mg 등)")
            times_str = st.text_input("복용 시간(HH:MM, 콤마 구분)", placeholder="08:00, 20:00")
            colA, colB = st.columns(2)
            with colA:
                start = st.date_input("시작일", value=local_today())
            with colB:
                end = st.date_input("종료일 (선택)", value=None)
            notes = st.text_area("메모")

            ok = st.form_submit_button("추가")

            if ok:
                valid_times = [t.strip() for t in times_str.split(",") if t.strip()]
                if not drug.strip() or not valid_times:
                    st.error("약 이름과 복용 시간은 필수입니다.")
                else:
                    new_med = {
                        "id": str(uuid.uuid4()),
                        "pet_id": pet["id"],
                        "drug": drug.strip(),
                        "dose": dose.strip(),
                        "unit": unit.strip(),
                        "times": valid_times,
                        "start": start.isoformat(),
                        "end": end.isoformat() if end else "",
                        "notes": notes.strip(),
                    }
                    st.session_state.med_schedule.append(new_med)
                    save_json(MED_FILE, st.session_state.med_schedule)
                    st.success("복약 스케줄이 추가되었습니다!")
                    st.rerun()

        # -------- 등록된 스케줄 목록 --------
        st.subheader("등록된 스케줄 관리")
        if not meds:
            st.info("등록된 복약 스케줄 없음")
        else:
            for m in meds:
                with st.expander(f"{m['drug']} ({', '.join(m['times'])})"):
                    st.write(f"기간: **{m['start']}** ~ **{m['end'] or '지속'}**")
                    st.write(f"용량: **{m['dose']}{m['unit']}**")
                    if m["notes"]:
                        st.caption(m["notes"])

                    if st.button("삭제", key=f"del_med_{m['id']}"):
                        st.session_state.med_schedule = [
                            x for x in st.session_state.med_schedule if x["id"] != m["id"]
                        ]
                        save_json(MED_FILE, st.session_state.med_schedule)
                        
                        keys_to_delete = [k for k in st.session_state.med_log if k.startswith(pet["id"])]
                        for key in keys_to_delete:
                            st.session_state.med_log[key] = {
                                log_key: log_value 
                                for log_key, log_value in st.session_state.med_log[key].items() 
                                if not log_key.startswith(m['id'])
                            }
                            if not st.session_state.med_log[key]:
                                del st.session_state.med_log[key]
                        save_json(MED_LOG_FILE, st.session_state.med_log)
                        
                        st.warning("스케줄이 삭제되었습니다.")
                        st.rerun()


# ========================= 5) 병원 일정 =========================
elif page == "병원 일정":
    st.header("🏥 병원 일정 관리")

    pet = pet_selector()
    if pet:

        # -------- 일정 추가 --------
        st.subheader("새 일정 추가")
        with st.form("hosp_form", clear_on_submit=True):
            title = st.text_input("제목*")
            colA, colB = st.columns(2)
            with colA:
                d = st.date_input("날짜", value=local_today())
            with colB:
                t = st.time_input("시간", value=time(10, 0))

            place = st.text_input("장소")
            notes = st.text_area("메모")

            ok = st.form_submit_button("추가")

            if ok:
                if not title.strip():
                    st.error("제목은 필수입니다.")
                else:
                    dt_iso = datetime.combine(d, t).isoformat()
                    new_event = {
                        "id": str(uuid.uuid4()),
                        "pet_id": pet["id"],
                        "title": title.strip(),
                        "dt": dt_iso,
                        "place": place.strip(),
                        "notes": notes.strip(),
                    }
                    st.session_state.hospital_events.append(new_event)
                    save_json(HOSP_FILE, st.session_state.hospital_events)
                    st.success("일정이 추가되었습니다!")
                    st.rerun()

        # -------- 일정 목록 --------
        st.subheader("다가오는 일정")
        events = [
            e for e in st.session_state.hospital_events
            if e["pet_id"] == pet["id"]
        ]
        events = sorted(events, key=lambda x: x["dt"])

        if not events:
            st.info("등록된 일정이 없습니다.")
        else:
            for e in events:
                try:
                    dt_obj = datetime.fromisoformat(e["dt"])
                    dt_kst = dt_obj.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    dt_kst = e["dt"]

                st.write(f"**{dt_kst}** — **{e['title']}** ({e.get('place', '장소 미정')})")
                if e.get("notes"):
                    st.caption(e["notes"])

                if st.button("삭제", key=f"del_evt_{e['id']}"):
                    st.session_state.hospital_events = [
                        x for x in st.session_state.hospital_events if x["id"] != e["id"]
                    ]
                    save_json(HOSP_FILE, st.session_state.hospital_events)
                    st.warning("삭제되었습니다.")
                    st.rerun()


# ========================= 6) 위험 정보 검색 =========================
elif page == "위험 정보 검색":
    st.header("⚠️ 위험 음식 / 식물 / 물품 검색")

    query = st.text_input("검색어 입력")

    db = pd.DataFrame(st.session_state.unsafe_db)

    if query.strip():
        # 이름, 분류, 이유 필드 전체에서 검색
        mask = (
            db["name"].str.contains(query, case=False, na=False) |
            db["category"].str.contains(query, case=False, na=False) |
            db["why"].str.contains(query, case=False, na=False)
        )
        view = db[mask]
    else:
        view = db

    view = view.rename(columns={"category": "분류", "name": "이름", "risk": "위험도", "why": "이유"})
    st.dataframe(view.sort_values(["분류", "위험도"]))

    # ------ 항목 추가 ------
    with st.expander("항목 추가"):
        with st.form("unsafe_add", clear_on_submit=True):
            cat = st.selectbox("분류", ["음식", "식물", "물품"])
            nm = st.text_input("이름")
            rk = st.selectbox("위험도", ["주의", "중간-고위험", "고위험"])
            why = st.text_area("이유")

            if st.form_submit_button("추가"):
                if not nm.strip() or not why.strip():
                    st.error("이름과 이유는 필수입니다.")
                else:
                    st.session_state.unsafe_db.append({
                        "category": cat,
                        "name": nm.strip(),
                        "risk": rk,
                        "why": why.strip(),
                    })
                    save_json(UNSAFE_FILE, st.session_state.unsafe_db)
                    st.success("추가 완료!")
                    st.rerun()

# ========================= 8) 관리자 대시보드 =========================
elif page == "관리자 대시보드":
    # 💡 관리자 권한 체크
    if not is_admin(st.session_state.user):
        st.error("관리자만 접근 가능합니다.")
        st.stop()

    st.header("👑 관리자 대시보드")

    # 1. 시스템 상태 요약
    st.subheader("시스템 데이터 요약")
    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("총 반려동물 수", len(st.session_state.pets))
    with colB:
        st.metric("총 복약 스케줄", len(st.session_state.med_schedule))
    with colC:
        st.metric("총 사료 로그 항목", len(st.session_state.feed_df))
    
    st.divider()

    # 2. 사용자 관리 섹션
    st.subheader("회원 관리")
    users = load_json(USER_FILE, [])

    if not users:
        st.info("등록된 회원이 없습니다.")
    else:
        st.write(f"총 회원 수: **{len(users)}**")
        
        # 관리자 계정 제외한 사용자 목록 표시
        user_list_to_display = [u for u in users if u["username"] != st.session_state.user]
        
        if user_list_to_display:
            st.warning("⚠️ 사용자 삭제 시 복구가 불가능하며, 해당 사용자의 반려동물 데이터는 남습니다. (수동 삭제 필요)")
            
            for u in user_list_to_display:
                col_user, col_del = st.columns([6, 1])
                
                with col_user:
                    st.write(f"**ID:** **{u['username']}** (일반 사용자)")
                
                with col_del:
                    if st.button("삭제", key=f"delete_user_{u['username']}"):
                        # 1) 사용자 데이터 삭제
                        users = [x for x in users if x["username"] != u["username"]]
                        save_json(USER_FILE, users)
                        
                        st.success(f"사용자 '{u['username']}'가 삭제되었습니다. 해당 사용자의 반려동물 데이터는 'pets.json' 파일에 남아있습니다.")
                        st.rerun()
        else:
             st.info("관리자를 제외한 사용자가 없습니다.")


# ========================= 7) 데이터 관리 =========================
elif page == "데이터 관리":
    st.header("🗂️ 데이터 관리")

    st.write("⚠ 데이터 초기화 시 복구가 불가능합니다.")

    colA, colB = st.columns(2)

    with colA:
        if st.button("사료/급수 로그 초기화"):
            st.session_state.feed_df = pd.DataFrame(columns=feed_cols)
            st.session_state.water_df = pd.DataFrame(columns=water_cols)
            save_csv(FEED_FILE, st.session_state.feed_df)
            save_csv(WATER_FILE, st.session_state.water_df)
            st.success("사료/급수 로그 초기화 완료!")
            st.rerun()

    with colB:
        if st.button("프로필 / 복약 / 병원 / 위험정보 초기화"):
            save_json(PET_FILE, [])
            save_json(MED_FILE, [])
            save_json(MED_LOG_FILE, {})
            save_json(HOSP_FILE, [])
            
            default_unsafe_reset = [{"category": "음식", "name": "초콜릿", "risk": "고위험", "why": "카카오 테오브로민 독성"}] 
            save_json(UNSAFE_FILE, default_unsafe_reset)
            
            st.session_state.pets = []
            st.session_state.med_schedule = []
            st.session_state.med_log = {}
            st.session_state.hospital_events = []
            st.session_state.unsafe_db = default_unsafe_reset
            
            st.success("모든 데이터 초기화 완료!")
            st.rerun()

    st.divider()
    st.subheader("📁 저장 파일 위치")
    st.code(
        f"{PET_FILE}\n"
        f"{FEED_FILE}\n"
        f"{WATER_FILE}\n"
        f"{MED_FILE}\n"
        f"{MED_LOG_FILE}\n"
        f"{HOSP_FILE}\n"
        f"{UNSAFE_FILE}"
    )


# ========================= 푸터 =========================
st.divider()
st.caption("© 2025 PetMate — 포트폴리오용 샘플 앱")