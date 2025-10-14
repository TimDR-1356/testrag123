# test-rag
chainlit, langchain_community, llama-cpp-python

pip install watchdog
watchmedo auto-restart --patterns="*.py" --recursive -- python -m chainlit run chainlit_app.py
