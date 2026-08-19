from app.ingestion.text_cleaner import clean_text


raw_text = """
    Product:     Industrial Router


    SKU:     RT-1001


    Manufacturer:      Cisco


    Category:    Networking
"""


cleaned_text = clean_text(raw_text)


print("RAW TEXT:")
print(repr(raw_text))

print("\nCLEANED TEXT:")
print(cleaned_text)