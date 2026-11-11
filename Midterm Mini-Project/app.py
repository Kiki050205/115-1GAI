
import json
import os
import urllib.error
import urllib.request
import streamlit as st

APP_TITLE = "📚 AI 作業與考試規劃助手"
MAX_CHARS = 6000

st.set_page_config(page_title="AI 作業與考試規劃助手", page_icon="📚")

INSTRUCTIONS = """
你是大學生的作業與考試公告整理助手。
只根據使用者貼上的公告整理資訊，不得自行編造。
找不到的截止日期請填「未知」。
相對日期（例如下週五）必須保留原文，不可自行推算。
如果公告包含多項作業或考試，必須分別整理。
task_type 只能使用「作業」、「考試」或「其他」。
todo_items 必須是根據公告可確認的待辦事項。
資訊不足時，請在 missing_info 列出需要確認的資訊。
所有回答使用繁體中文。
"""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "task_name": {"type": "string"},
                    "task_type": {
                        "type": "string",
                        "enum": ["作業", "考試", "其他"]
                    },
                    "deadline": {"type": "string"},
                    "todo_items": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": [
                    "task_name",
                    "task_type",
                    "deadline",
                    "todo_items"
                ],
                "additionalProperties": False
            }
        },
        "missing_info": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["tasks", "missing_info"],
    "additionalProperties": False
}


def get_setting(name, default=""):
    try:
        value = st.secrets.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


def validate_result(data):
    if not isinstance(data, dict):
        raise ValueError("AI 回傳的資料不是物件。")

    if set(data.keys()) != {"tasks", "missing_info"}:
        raise ValueError("AI 回傳的主要欄位不正確。")

    if not isinstance(data["tasks"], list):
        raise ValueError("tasks 必須是清單。")

    if not isinstance(data["missing_info"], list):
        raise ValueError("missing_info 必須是清單。")

    if not all(isinstance(x, str) for x in data["missing_info"]):
        raise ValueError("missing_info 的內容格式錯誤。")

    for task in data["tasks"]:
        if not isinstance(task, dict):
            raise ValueError("任務資料格式錯誤。")

        expected = {
            "task_name", "task_type", "deadline", "todo_items"
        }

        if set(task.keys()) != expected:
            raise ValueError("任務欄位不完整。")

        if not all(
            isinstance(task[key], str)
            for key in ["task_name", "task_type", "deadline"]
        ):
            raise ValueError("任務文字欄位格式錯誤。")

        if task["task_type"] not in ["作業", "考試", "其他"]:
            raise ValueError("任務類型不正確。")

        if not isinstance(task["todo_items"], list):
            raise ValueError("待辦事項必須是清單。")

        if not all(isinstance(x, str) for x in task["todo_items"]):
            raise ValueError("待辦事項內容格式錯誤。")

    return data


def call_openai(announcement):
    api_key = get_setting("OPENAI_API_KEY")
    model = get_setting("OPENAI_MODEL", "gpt-5.4-mini")

    if not api_key:
        raise ValueError(
            "找不到 OPENAI_API_KEY，請先設定 API 金鑰。"
        )

    payload = {
        "model": model,
        "instructions": INSTRUCTIONS,
        "input": announcement,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "student_task_planner",
                "strict": True,
                "schema": OUTPUT_SCHEMA
            }
        }
    }

    request = urllib.request.Request(
        url="https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"API 請求失敗（HTTP {error.code}），請檢查模型、"
            "金鑰及 API 額度。"
        ) from error

    except urllib.error.URLError as error:
        raise RuntimeError(
            "無法連線到 OpenAI API，請檢查網路。"
        ) from error

    if result.get("status") != "completed":
        raise RuntimeError("AI 回應未完成，請稍後重試。")

    output_texts = []

    for item in result.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") == "refusal":
                    raise RuntimeError("AI 拒絕處理這項請求。")
                if content.get("type") == "output_text":
                    output_texts.append(content.get("text", ""))

    if len(output_texts) != 1:
        raise RuntimeError("AI 沒有回傳單一有效的結構化結果。")

    data = json.loads(output_texts[0])
    return validate_result(data), model


st.title(APP_TITLE)
st.write(
    "貼上老師的作業或考試公告，AI 幫你整理"
    "重要時間、待辦事項及需要確認的資訊。"
)

if "record" not in st.session_state:
    st.session_state.record = None

if "request_count" not in st.session_state:
    st.session_state.request_count = 0

with st.form("planner_form"):
    announcement = st.text_area(
        "請貼上作業或考試公告",
        height=200,
        placeholder="例如：資料庫期中報告下週五截止，"
                    "需要繳交 ER 圖、10 題 SQL 查詢及心得。"
    )

    api_enabled = st.checkbox(
        "我同意啟用 OpenAI API（可能產生費用）",
        value=False
    )

    submitted = st.form_submit_button("📋 開始整理")

if submitted:
    st.session_state.record = None

    if not announcement.strip():
        st.error("請先輸入作業或考試公告。")

    elif len(announcement) > MAX_CHARS:
        st.error("公告內容超過 6000 字元，請縮短後再提交。")

    elif not api_enabled:
        st.warning("API 目前關閉，請勾選啟用後再提交。")

    else:
        try:
            with st.spinner("AI 正在整理公告..."):
                st.session_state.request_count += 1
                data, model = call_openai(announcement)

            st.session_state.record = {
                "original": announcement,
                "data": data,
                "model": model
            }

            st.success("整理完成！")

        except Exception as error:
            st.error(f"處理失敗：{error}")

record = st.session_state.record

if record is not None:
    st.subheader("📌 整理結果")

    for index, task in enumerate(record["data"]["tasks"], start=1):
        with st.container(border=True):
            st.markdown(f"### 任務 {index}")
            st.write("**名稱：**", task["task_name"])
            st.write("**類型：**", task["task_type"])
            st.write("**截止日期：**", task["deadline"])

            st.write("**待辦事項：**")
            if task["todo_items"]:
                for todo in task["todo_items"]:
                    st.write("☐", todo)
            else:
                st.write("沒有可確認的待辦事項。")

    st.subheader("❓ 需要確認的資訊")
    if record["data"]["missing_info"]:
        for item in record["data"]["missing_info"]:
            st.write("•", item)
    else:
        st.write("沒有需要額外確認的資訊。")

    with st.expander("查看 JSON 結構化輸出"):
        st.json(record["data"])

    st.caption(f"使用模型：{record['model']}")

st.caption(
    f"本次網頁工作階段的 API 呼叫嘗試次數："
    f"{st.session_state.request_count}"
)
