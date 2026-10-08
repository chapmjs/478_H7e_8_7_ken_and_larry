Ken & Larry Ice Cream Production Optimizer
An interactive Streamlit app for the Ken and Larry, Inc. linear-programming and sensitivity-analysis exercise.
Run locally
pip install -r requirements.txt
streamlit run app.py
Deploy with GitHub and Streamlit Community Cloud
1. Create a GitHub repository.
2. Upload app.py, requirements.txt, and README.md.
3. In Streamlit Community Cloud, choose Create app.
4. Select the repository, branch, and app.py as the main file.
5. Deploy.
The app includes the original LP, an interactive solver, resource-usage charts, and answer tabs for parts (a)–(f). The textbook explanations use the original solution and sensitivity logic, including the important warning that the 15-pound sugar purchase exceeds the original allowable-increase range.
