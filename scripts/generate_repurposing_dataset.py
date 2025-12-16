import pandas as pd
import numpy as np
import os

# Define the list of cases
# Each case: (Drug, Original_Indication, New_Indication, Outcome, Phase_Started, Mechanism_Score_Est)
# Outcome: 1 = Success, 0 = Failure
# Phase_Started: 'Discovery', 'Phase1', 'Phase2', 'Phase3'
# Mechanism_Score: 1-10 integer estimate

cases = [
    # SUCCESSES
    ("Metformin", "Diabetes Type 2", "PCOS", 1, "Phase2", 8),
    ("Thalidomide", "Sedative", "Leprosy", 1, "Discovery", 9),
    ("Thalidomide", "Leprosy", "Multiple Myeloma", 1, "Phase2", 10),
    ("Sildenafil", "Angina", "Erectile Dysfunction", 1, "Phase1", 10),
    ("Sildenafil", "Erectile Dysfunction", "Pulmonary Hypertension", 1, "Phase3", 9),
    ("Minoxidil", "Hypertension", "Hair Loss", 1, "Phase1", 10),
    ("Zidovudine (AZT)", "Cancer", "HIV/AIDS", 1, "Discovery", 9),
    ("Tamoxifen", "Breast Cancer", "Bipolar Disorder", 1, "Phase2", 6),
    ("Raloxifene", "Osteoporosis", "Breast Cancer", 1, "Phase3", 8),
    ("Sirolimus (Rapamycin)", "Organ Transplant", "LAM (Lung Disease)", 1, "Phase2", 7),
    ("Adalimumab", "RA (failed Septic Shock)", "Rheumatoid Arthritis", 1, "Phase3", 9), # Originally failed septic shock
    ("Infliximab", "Sepsis", "Crohn's Disease", 1, "Phase2", 9),
    ("Hydroxychloroquine", "Malaria", "Rheumatoid Arthritis", 1, "Phase2", 7),
    ("Hydroxychloroquine", "Malaria", "Lupus (SLE)", 1, "Phase2", 7),
    ("Methotrexate", "Leukemia", "Rheumatoid Arthritis", 1, "Discovery", 8),
    ("Methotrexate", "Leukemia", "Psoriasis", 1, "Discovery", 8),
    ("Finasteride", "BPH", "Hair Loss", 1, "Phase2", 10),
    ("Duloxetine", "Depression", "Neuropathic Pain", 1, "Phase3", 7),
    ("Bupropion", "Depression", "Smoking Cessation", 1, "Phase1", 8),
    ("Gabapentin", "Epilepsy", "Neuropathic Pain", 1, "Discovery", 6),
    ("Pregabalin", "Epilepsy", "Fibromyalgia", 1, "Phase2", 6),
    ("Ketoconazole", "Fungal Infection", "Cushing's Syndrome", 1, "Discovery", 7),
    ("Spironolactone", "Hypertension", "Acne", 1, "Phase2", 8),
    ("Spironolactone", "Hypertension", "Hirsutism", 1, "Phase2", 8),
    ("Topiramate", "Epilepsy", "Migraine", 1, "Phase2", 7),
    ("Topiramate", "Epilepsy", "Obesity", 1, "Phase2", 6),
    ("Amantadine", "Influenza", "Parkinson's Disease", 1, "Discovery", 9),
    ("Gemcitabine", "Antiviral", "Cancer", 1, "Discovery", 5), # Failed antiviral
    ("Rituximab", "Lymphoma", "Rheumatoid Arthritis", 1, "Phase2", 8),
    ("Dimethyl fumarate", "Psoriasis", "Multiple Sclerosis", 1, "Phase3", 7),
    ("Fingolimod", "Transplant Rejection", "Multiple Sclerosis", 1, "Phase2", 7),
    ("Bromocriptine", "Parkinson's", "Diabetes Type 2", 1, "Phase3", 6),
    ("Colesevelam", "Hypercholesterolemia", "Diabetes Type 2", 1, "Phase3", 5),
    ("Milnacipran", "Depression", "Fibromyalgia", 1, "Phase3", 6),
    ("Dapoxetine", "Depression", "Premature Ejaculation", 1, "Phase2", 7),
    ("Aspirin", "Pain", "Cardiovascular Prevention", 1, "Phase3", 9),
    ("Botulinum Toxin", "Strabismus", "Migraine", 1, "Discovery", 8),
    ("Botulinum Toxin", "Strabismus", "Cosmetic Wrinkles", 1, "Discovery", 10),
    ("Pemetrexed", "Cancer", "Mesothelioma", 1, "Phase2", 8), # Broadening
    ("Imatinib", "CML", "GIST", 1, "Phase2", 10),
    
    # FAILURES
    ("Metformin", "Diabetes", "Cancer", 0, "Phase3", 7),
    ("Ivermectin", "Parasites", "COVID-19", 0, "Phase3", 3),
    ("Hydroxychloroquine", "Malaria", "COVID-19", 0, "Phase3", 4),
    ("Lopinavir/Ritonavir", "HIV", "COVID-19", 0, "Phase3", 5),
    ("Canakinumab", "Arthritis", "Lung Cancer (NSCLC)", 0, "Phase3", 6),
    ("Canakinumab", "Arthritis", "Cardiovascular Disease", 0, "Phase3", 6),
    ("Verdiperstat", "MSA", "ALS", 0, "Phase3", 5),
    ("Azeliragon", "Alzheimer's", "Diabetic Nephropathy", 0, "Phase2", 4),
    ("Lonafarnib", "Progeria", "Solid Tumors", 0, "Phase2", 6),
    ("Rosiglitazone", "Diabetes", "Cancer", 0, "Phase2", 5),
    ("Pioglitazone", "Diabetes", "Cancer", 0, "Phase2", 5),
    ("Latrepirdine", "Allergy", "Alzheimer's", 0, "Phase2", 4),
    ("Lithium", "Bipolar", "ALS", 0, "Phase2", 5),
    ("Ceftriaxone", "Antibacterial", "ALS", 0, "Phase3", 6),
    ("Minocycline", "Antibacterial", "ALS", 0, "Phase3", 5),
    ("Erythropoietin", "Anemia", "Stroke", 0, "Phase3", 7),
    ("Progesterone", "Support Pregnancy", "Traumatic Brain Injury", 0, "Phase3", 6),
    ("Magnesium Sulfate", "Eclampsia", "Stroke", 0, "Phase3", 5),
    ("Albumin", "Volume Expansion", "Stroke", 0, "Phase3", 5),
    ("Simvastatin", "Hypercholesterolemia", "Multiple Sclerosis", 0, "Phase2", 6),
    ("Rofecoxib", "Pain", "Cancer Prevention", 0, "Phase3", 7), # Withdrawn for safety
    ("Aprepitant", "Nausea", "Depression", 0, "Phase3", 6),
    ("Mifepristone", "Abortion", "Psychotic Depression", 0, "Phase3", 5),
    ("Saracatinib", "Cancer", "Alzheimer's", 0, "Phase2", 6),
    ("Intravenous Immunoglobulin", "Immune Deficiency", "Alzheimer's", 0, "Phase3", 5),
    ("Gefitinib", "Lung Cancer", "Breast Cancer", 0, "Phase2", 4),
    ("Everolimus", "Transplant", "Hepatocellular Carcinoma", 0, "Phase3", 6),
    ("Sunitinib", "Cancer", "Breast Cancer", 0, "Phase3", 5),
    ("Sorafenib", "Cancer", "Lung Cancer", 0, "Phase3", 5),
    ("Bevacizumab", "Cancer", "Gastric Cancer", 0, "Phase3", 5)
]

def generate_dataset():
    data_rows = []
    
    # Random seed for reproducibility
    np.random.seed(42)

    for case in cases:
        drug, orig, new, outcome, phase, mech_score = case
        
        # Feature Engineering (Simulation)
        
        # Molecular Similarity (0 - 1)
        # Successes might have slightly higher similarity or distinct patterns, 
        # but often repurposing is serendipitous (low similarity to orig mechanism's goal)
        # We'll map it randomly but loosely correlated with mechanism score
        base_sim = np.random.uniform(0.3, 0.9)
        if outcome == 1:
            # Slight boost for successes to simulate "better fit"
            molecular_similarity = min(1.0, base_sim + np.random.uniform(-0.1, 0.1))
        else:
            molecular_similarity = max(0.0, base_sim + np.random.uniform(-0.15, 0.05))
            
        # Disease Category Match (Boolean)
        # Simple heuristic: look for keyword matches
        # This is a rough approximation
        keywords = ["Cancer", "Tumor", "Leukemia", "Lymphoma", "Carcinoma", 
                    "Diabetes", "Metabolic", "Arthritis", "Pain", "Depression", 
                    "Infection", "Viral", "Bacterial", "Fungal"]
        
        cat_match = False
        for k in keywords:
            if (k in orig and k in new):
                cat_match = True
                break
        
        # Market Size Ratio (New / Old)
        # Successes often target large new markets (e.g. Viagra, Rogaine)
        if outcome == 1:
            market_size_ratio = np.random.lognormal(mean=0.5, sigma=0.8) # Skewed towards > 1
        else:
            market_size_ratio = np.random.lognormal(mean=0.0, sigma=0.8)
            
        # Mechanism Strength (1-10)
        # Use the hand-coded score but add slight noise
        mechanism_strength = max(1, min(10, int(mech_score + np.random.randint(-1, 2))))
        
        # Prior Safety Data (Years)
        # Most repurposing candidates have > 5 years, some > 20
        prior_safety_data = np.random.choice([5, 8, 10, 15, 20, 25, 30, 40, 50])
        
        row = {
            "drug_name": drug,
            "original_indication": orig,
            "new_indication": new,
            "molecular_similarity": round(molecular_similarity, 3),
            "phase_started": phase,
            "disease_category_match": cat_match,
            "market_size_ratio": round(market_size_ratio, 2),
            "mechanism_strength": mechanism_strength,
            "prior_safety_data": prior_safety_data,
            "outcome": outcome
        }
        data_rows.append(row)

    df = pd.DataFrame(data_rows)
    
    # Save to CSV
    output_path = os.path.join("data", "repurposing_training_data.csv")
    os.makedirs("data", exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Dataset generated with {len(df)} rows at {output_path}")
    print(df.head())
    print(df['outcome'].value_counts())

if __name__ == "__main__":
    generate_dataset()
