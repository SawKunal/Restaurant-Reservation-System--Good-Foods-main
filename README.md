# 🍽️ GoodFoods AI Restaurant Reservation Agent

An intelligent conversational AI agent for seamless restaurant reservations, powered by **Groq LLaMA 3.1**.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![Groq](https://img.shields.io/badge/Groq-LLM-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📌 Overview

GoodFoods AI Restaurant Reservation Agent is a conversational AI system designed to automate restaurant bookings through natural language conversations.  
It supports restaurant search, availability checks, reservations, and cancellations with **low-latency LLM inference**.

---

## ✨ Features

- Conversational restaurant booking
- Multi-turn dialogue support
- Tool-first, zero-hallucination design
- Sub-second response times using Groq
- Interactive Streamlit UI

---

## 🛠️ Tech Stack

- **Language:** Python
- **Frontend:** Streamlit
- **LLM:** Groq LLaMA 3.1 (8B Instant)
- **Prompting:** Tool-based MCP architecture

---

## 🚀 Setup Instructions

```bash
git clone https://github.com/<your-username>/goodfoods-restaurant-reservation-agent.git
cd goodfoods-restaurant-reservation-agent
pip install -r requirements.txt
streamlit run frontend/app.py
