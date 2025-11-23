# Quick Start Guide - Professional Crop Consulting System

## Get Running in 5 Minutes

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Start the API Server

```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Test the API

Open your browser and go to: **http://localhost:8000/docs**

You'll see the interactive API documentation (Swagger UI).

### Step 4: Try Your First Identification

Click on `POST /api/v1/identify/pest` → "Try it out"

Use this example request:

```json
{
  "crop": "soybean",
  "growth_stage": "R3",
  "symptoms": ["curled_leaves", "yellowing", "sticky_residue"]
}
```

Click "Execute" and you'll get professional pest identification results!

### Step 5: Get a Spray Recommendation

Try `POST /api/v1/recommend/spray`:

```json
{
  "crop": "soybean",
  "growth_stage": "R3",
  "problem_type": "pest",
  "problem_id": 0,
  "severity": 8,
  "field_acres": 160,
  "previous_applications": []
}
```

You'll get:
- Product recommendations
- Application rates
- Economic analysis
- Resistance management notes
- Spray timing guidance

## 🎯 Real-World Example

**Scenario**: You found aphids in a soybean field

1. **Identify the pest** → POST /api/v1/identify/pest
   - Confirms: Soybean Aphid
   - Economic threshold: 250/plant

2. **Check if treatment warranted** → POST /api/v1/threshold/check
   - Population: 300/plant
   - Result: TREAT (net benefit $15/acre)

3. **Get spray recommendation** → POST /api/v1/recommend/spray
   - Product: Warrior II at 2.56 oz/acre
   - Cost: $17.50/acre total
   - ROI: 86%

4. **Check weather** → GET /api/v1/weather/spray-window
   - Best window: Tomorrow morning
   - Rating: 9/10

**Done!** Professional recommendation in seconds.

## 📱 Next Steps

1. Read **PROFESSIONAL_SYSTEM_GUIDE.md** for complete documentation
2. Explore all API endpoints at http://localhost:8000/docs
3. Test with your real field scenarios
4. Build a simple frontend or use existing desktop apps
5. Integrate with your workflow

## 🆘 Troubleshooting

**Import errors?**
```bash
pip install --upgrade -r requirements.txt
```

**Port already in use?**
Edit `main.py` and change port:
```python
uvicorn.run("main:app", host="0.0.0.0", port=8001)
```

**Need help?**
Check the example usage at bottom of each service file:
```bash
python services/spray_recommender.py
python services/pest_identification.py
```

## 🚀 You're Ready!

This is a professional-grade system. Start using it, refine it based on field experience, and build your consulting business around it.

The knowledge base contains:
- 23 corn pests & diseases
- 23 soybean pests & diseases
- 40+ pesticide products
- Economic thresholds
- Real label information

**This is valuable. Use it wisely.**
