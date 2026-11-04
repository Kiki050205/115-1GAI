
import os
import json
import streamlit as st
from openai import OpenAI
from pydantic import BaseModel, Field


# =========================
# 1. 網頁基本設定
# =========================

st.set_page_config(
    page_title="AI 活動公告整理器",
    page_icon="📢",
    layout="centered"
)

st.title("📢 AI 活動公告整理器")

st.write(
    "貼上一段活動公告，AI 幫你整理活動資訊。"
)


# =========================
# 2. Structured Outputs
# =========================

class EventResult(BaseModel):
    event_name: str = Field(
        description="活動名稱；原文沒有提供時填未知"
    )

    event_date: str = Field(
        description="活動日期；原文沒有提供時填未知"
    )

    location: str = Field(
        description="活動地點；原文沒有提供時填未知"
    )

    registration_deadline: str = Field(
        description="報名截止日期；原文沒有提供時填未知"
    )

    missing_info: list[str] = Field(
        description="原文缺少的重要活動資訊"
    )


# =========================
# 3. 初始化結果保存
# =========================

if "record" not in st.session_state:
    st.session_state.record = None

if "error" not in st.session_state:
    st.session_state.error = None


# =========================
# 4. 使用者輸入
# =========================

with st.form("event_form"):

    announcement = st.text_area(
        "請貼上活動公告",
        height=220,
        placeholder="例如：本週五下午三點在世新大學舉辦社團迎新活動，請於週三前報名。"
    )

    api_enabled = st.checkbox(
        "我同意啟用 OpenAI API",
        value=False
    )

    submitted = st.form_submit_button(
        "整理活動公告",
        type="primary"
    )


# =========================
# 5. 送出與檢查
# =========================

if submitted:

    # 新提交先清除舊結果
    st.session_state.record = None
    st.session_state.error = None

    # 檢查空白
    if not announcement.strip():

        st.session_state.error = "請先輸入活動公告。"

    # 檢查長度
    elif len(announcement) > 6000:

        st.session_state.error = (
            "公告內容超過 6000 字，請縮短後再提交。"
        )

    # 檢查 API 開關
    elif not api_enabled:

        st.session_state.error = (
            "請先勾選啟用 OpenAI API。"
        )

    # 通過輸入檢查
    else:

        try:

            # 取得 API 金鑰
            api_key = st.secrets.get(
                "OPENAI_API_KEY",
                os.getenv("OPENAI_API_KEY", "")
            )

            if not api_key:

                raise ValueError(
                    "找不到 OpenAI API 金鑰，"
                    "請檢查 .env 或 Streamlit Secrets。"
                )

            # 建立 OpenAI 客戶端
            client = OpenAI(
                api_key=api_key,
                timeout=60.0,
                max_retries=0
            )

            # 呼叫 Structured Outputs
            response = client.responses.parse(
                model=os.getenv(
                    "OPENAI_MODEL",
                    "gpt-5.4-mini"
                ),
                input=[
                    {
                        "role": "system",
                        "content": (
                            "你是活動公告整理助手。"
                            "只能根據使用者提供的原文整理資訊。"
                            "禁止自行補造活動名稱、日期、地點或報名截止日。"
                            "如果原文沒有提供資訊，請填未知。"
                            "missing_info 列出原文缺少的重要資訊。"
                            "使用繁體中文。"
                        )
                    },
                    {
                        "role": "user",
                        "content": announcement
                    }
                ],
                text_format=EventResult
            )

            # 檢查是否有拒答
            if response.output_parsed is None:

                raise ValueError(
                    "模型沒有提供可用的結構化結果。"
                )

            # 取得 Pydantic 結果
            data = response.output_parsed.model_dump()

            # 檢查欄位
            required_fields = [
                "event_name",
                "event_date",
                "location",
                "registration_deadline",
                "missing_info"
            ]

            if not all(
                field in data
                for field in required_fields
            ):

                raise ValueError(
                    "模型回應缺少必要欄位。"
                )

            # 保存成功結果
            st.session_state.record = {
                "original": announcement,
                "data": data
            }

        except Exception as e:

            st.session_state.error = (
                f"處理失敗：{type(e).__name__}：{e}"
            )


# =========================
# 6. 顯示錯誤
# =========================

if st.session_state.error:

    st.error(st.session_state.error)


# =========================
# 7. 顯示成功結果
# =========================

if st.session_state.record:

    record = st.session_state.record

    data = record["data"]

    st.success("活動公告整理完成！")

    st.subheader("📋 活動資訊")

    st.write("**活動名稱：**", data["event_name"])

    st.write("**活動日期：**", data["event_date"])

    st.write("**活動地點：**", data["location"])

    st.write(
        "**報名截止日期：**",
        data["registration_deadline"]
    )

    st.subheader("⚠️ 缺少的資訊")

    if data["missing_info"]:

        for item in data["missing_info"]:

            st.write(f"- {item}")

    else:

        st.write("沒有列出缺少的重要資訊。")

    with st.expander("查看原始公告"):

        st.text(record["original"])

    with st.expander("查看完整 JSON"):

        st.json(data)
