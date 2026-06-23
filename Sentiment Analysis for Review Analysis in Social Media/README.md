Sentiment Analyzer - No Kafka (Sample Mode)

How to run:
1. unzip the folder
2. python -m venv venv
3. source venv/bin/activate   (Windows: venv\Scripts\Activate.ps1)
4. pip install -r requirements.txt
5. Edit config/.env and put your GEMINI_API_KEY
6. python run_project.py
7. Open http://localhost:7860 and paste reviews to analyze. History saved in data/reviews.db
