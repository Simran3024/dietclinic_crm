from django.shortcuts import render
import pymongo, certifi, os

def debug_leads(request):
    try:
        MONGO_URI = os.environ.get("MONGO_URI")
        if not MONGO_URI:
            raise Exception("MONGO_URI not set")

        client = pymongo.MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
        db = client["CRM"]
        leads_collection = db["leads"]

        leads = list(leads_collection.find())
        for lead in leads:
            lead["id"] = str(lead["_id"])

    except Exception as e:
        print("ERROR in debug_leads:", e)
        leads = []
    
    return render(request, "debug_leads.html", {"leads": leads})
