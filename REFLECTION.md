# Reflection

## 1. What makes your chatbot feel intelligent rather than just doing keyword search? What did you specifically do to get there?

The chatbot feels more intelligent because it understands the meaning of the query instead of only matching keywords. I used embeddings with FAISS vector search, which helps retrieve semantically related information from different documents. For example, a query about “employee growth” can still find content related to “headcount increase” even if the exact words are different.

I also added conversation memory so the chatbot can handle follow-up questions naturally. Instead of treating every question separately, it remembers previous context from the conversation.

Another thing I focused on was combining information across multiple files. The chatbot does not just return a single paragraph — it tries to summarize and compare data from annual reports, quarterly reports, Excel sheets, and stock data together. I also added source citations and automatic output selection (PDF or Excel) depending on the type of question.

---

## 2. Where does it still fall short? What would a real analyst notice that your system gets wrong or misses?

The system still has some limitations. Financial PDFs often contain complex tables and multi-column layouts, and sometimes the extracted text loses formatting or context. Because of this, some numerical comparisons may not be perfectly accurate.

Another issue is that the model can occasionally miss small details or slightly round numbers while summarizing.

The chatbot also does not deeply verify contradictions between documents. If two reports mention slightly different values, the system may not always highlight the difference automatically.

The Excel reports generated are useful for analysis, but they are still basic compared to professionally prepared analyst sheets with formulas, charts, and advanced formatting.

---

## 3. Which AI tools did you use to build this, and what did you have to fix or override yourself?

I used Google Gemini API for both response generation and embeddings. LangChain was used for the RAG pipeline, conversation handling, and document retrieval, while FAISS was used as the vector database for semantic search.

I also used Streamlit for the interface and Pandas for handling Excel and CSV files.

Most of the work was not just using libraries directly, but improving the behavior of the system. I had to tune chunk sizes for better retrieval, improve prompts so the chatbot gives structured financial answers, add citation handling, and create logic for deciding whether the output should be shown as normal text, PDF, or Excel.
