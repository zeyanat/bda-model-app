#requests lets Pythn send messages to web addresses (our endpoint)
import requests
#streamlit turns this Python script into a web page
import streamlit as st

#Big heading at the top of the page 
st.title("NYC restaurant inspection predictor")

# A paragraph telling visitors what the page does
st.write("Enter a restaurant's last inspection score and how many times it has been "
  "inspected. A model running on Databricks predicts its next score. Lower is better.")

# A number box for the last score: 0 to 100, starting at 12.0, going up in steps of 1
previous_score = st.number_input("Score at the last inspection", min_value=0.0,
                      max_value=100.0, value=12.0, step=1.0)
# A number box for how many inspections: 2 to 20, starting at 5.0
inspections = st.number_input("Number of inspections so far", min_value=2.0,
                      max_value=20.0, value=5.0, step=1.0)

# Everything indented under this line runs only when the Predict button is clicked
if st.button("Predict"):
  # Read the workspace address from the secret settings and remove any slash at the end
  host = st.secrets["DATABRICKS_HOST"].rstrip("/")
  # Build the endpoint's full web address from the host and the endpoint name
  url = f"{host}/serving-endpoints/{st.secrets['ENDPOINT_NAME']}/invocations"
  # Attach the token, which proves we are allowed to use the endpoint
  headers = {"Authorization": f"Bearer {st.secrets['DATABRICKS_TOKEN']}"}
  # Pack the two inputs in the format the endpoint expects: a list of rows
  body = {"dataframe_records": [{"previous_score": previous_score,
                      "inspections": inspections}]}
  
  # Show a spinning wheel while we wait for the answer
  with st.spinner("Asking the model. The first request can take a few minutes "
            "while the endpoint wakes up..."):
    # Try to send the request; wait up to 300 seconds for a reply
    try:
      r = requests.post(url, headers=headers, json=body, timeout=300)
    # If the request could not be sent at all (no internet, wrong address)...
    except requests.RequestException as e:
      # ...show the problem in a red box
      st.error(f"Could not reach the model: {e}")
      # ...and stop running the rest of the script
      st.stop()
    
# Status code 200 means the endpoint answered successfully
if r.status_code == 200:
    # Take the first (and only) prediction out of the reply
    score = r.json()["predictions"][0]
    # Turn the score into New York's grade: A is 0-13, B is 14-27, C is 28 or more
    grade = "A" if score <= 13 else "B" if score <= 27 else "C"
    # Show the result in a green box, rounded to one decimal place
    st.success(f"Predicted next score: {score:.1f}, which is grade {grade} territory")
# Any other status code means the endpoint answered with an error
else:
    # Show the error code and message in a red box
    st.error(f"The model replied with an error {r.status_code}: {r.text}")
  
# Small grey note at the bottom of the page
st.caption("This is a statistical guess from past scores. Only an inspection can tell "
      "you how clean a kitchen really is.")
