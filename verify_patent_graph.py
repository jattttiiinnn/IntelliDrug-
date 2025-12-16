from utils.patent_network import render_patent_network

def test_render():
    print("Testing render_patent_network...")
    patents = [
        {"patent_number": "US123", "title": "Test", "assignee": "TestCo", "status": "Active"}
    ]
    try:
        # This function generates HTML string using f-strings.
        # Calling it will trigger the NameError if not fixed.
        # It calls streamlit.components.v1.html internally, which might fail if no streamlit context?
        # Actually components.html just returns None or prints to streamlit. 
        # But we only care if the F-String evaluation passes.
        
        # We need to mock streamlit.components.v1 to avoid "No SessionContext" error if we just run this script?
        # Or just catch that error, but ensure we passed the f-string line.
        
        # Actually, let's just inspect the code or try to run it.
        # The f-string is evaluated BEFORE components.html is called.
        # render_patent_network -> f"""...""" -> NameError (if fail) -> components.html
        
        render_patent_network(patents, "Metformin")
        print("Success: No NameError during string formatting.")
        
    except NameError as ne:
        print(f"FAILED: NameError: {ne}")
    except Exception as e:
        # We expect StreamlitAPIException or similar if running outside streamlit, 
        # but that means f-string succeeded!
        print(f"Passed string formatting check. (Caught expected non-syntax error: {type(e).__name__})")

if __name__ == "__main__":
    test_render()
