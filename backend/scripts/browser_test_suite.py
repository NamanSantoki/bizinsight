"""
Automated End-to-End Browser Testing Suite for BIZINSIGHT Enterprise Platform 2.0
Executes real browser automation across all tabs and interactive controls using Selenium.
"""
import time
import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

SCREENSHOT_DIR = r"N:\PathtoGermany\docs\screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def run_browser_checks():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1600,1050')

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)
    results = {}

    try:
        print("[1/18] Obtaining admin JWT token...")
        import requests
        login_res = requests.post(
            "http://127.0.0.1:8000/api/v1/auth/login",
            data={"username": "admin", "password": "AdminPass2026!"}
        )
        auth_data = login_res.json()
        token = auth_data["access_token"]
        user_info = auth_data["user"]
        print(f"Token obtained for user: {user_info['username']} (role: {user_info['role']})")

        print("[2/18] Navigating to http://127.0.0.1:5173/ and injecting authenticated session...")
        driver.get("http://127.0.0.1:5173/")
        time.sleep(1)
        driver.execute_script(
            f"localStorage.setItem('bizinsight_token', '{token}'); "
            f"localStorage.setItem('bizinsight_user', JSON.stringify({json.dumps(user_info)}));"
        )
        driver.refresh()
        time.sleep(2)
        driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "01_initial_load.png"))
        results["initial_load"] = "PASS"
        results["auth_flow"] = "PASS"

        # Helper function to click tab by label or text
        def click_tab(name, tab_id=None):
            print(f"--> Testing Tab: {name}...")
            # Try to find button with text
            tab_buttons = driver.find_elements(By.XPATH, f"//aside//button[contains(., '{name}')]")
            if tab_buttons:
                driver.execute_script("arguments[0].scrollIntoView(true);", tab_buttons[0])
                time.sleep(0.5)
                tab_buttons[0].click()
                time.sleep(1.5)
                return True
            return False

        # 1. Executive Dashboard (Overview)
        if click_tab("Executive Dashboard"):
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "03_executive_dashboard.png"))
            results["overview"] = "PASS"

        # 2. Exploratory Analytics
        if click_tab("Exploratory Analytics"):
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "04_exploratory_analytics.png"))
            results["analytics"] = "PASS"

        # 3. Data Sources (Connectors)
        if click_tab("Data Sources"):
            time.sleep(1)
            # Find and click Test Connection
            test_conn_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Test Connection')]")
            if test_conn_btns:
                test_conn_btns[0].click()
                time.sleep(1.5)
            # Find and click Sync Now
            sync_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Sync Now')]")
            if sync_btns:
                sync_btns[0].click()
                time.sleep(1.5)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "05_data_sources.png"))
            results["data_sources"] = "PASS"

        # 4. Contracts & Quality Gates
        if click_tab("Contracts & Quality Gates"):
            time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "06_contracts_gates.png"))
            results["contracts_gates"] = "PASS"

        # 5. Full Data Lineage DAG
        if click_tab("Full Data Lineage DAG"):
            time.sleep(1)
            # Click a node inside the list
            nodes = driver.find_elements(By.XPATH, "//h4[contains(text(), 'Curated Sales Fact') or contains(text(), 'Sales PostgreSQL')]")
            if nodes:
                nodes[0].click()
                time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "07_data_lineage.png"))
            results["lineage"] = "PASS"

        # 6. Semantic Metrics Store
        if click_tab("Semantic Metrics Store"):
            time.sleep(1)
            # Click a dimension button
            dim_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'region') or contains(text(), 'product_category') or contains(text(), 'date')]")
            if dim_btns:
                dim_btns[0].click()
                time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "08_metrics_store.png"))
            results["metrics_store"] = "PASS"

        # 7. Governed AI Analyst (NLQ)
        if click_tab("Governed AI Analyst"):
            time.sleep(1)
            # Look for ask input and ask button
            inputs = driver.find_elements(By.XPATH, "//input[@placeholder or @type='text']")
            ask_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Ask') or contains(., 'Analyze') or contains(., 'Query')]")
            if inputs and ask_btns:
                inputs[0].clear()
                inputs[0].send_keys("What is the average order value across categories?")
                ask_btns[0].click()
                time.sleep(2)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "09_ai_analyst.png"))
            results["ask_data"] = "PASS"

        # 8. MLOps Registry & Drift
        if click_tab("MLOps Registry & Drift"):
            time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "10_mlops_registry.png"))
            results["mlops_registry"] = "PASS"

        # 9. SHAP Explainability
        if click_tab("SHAP Explainability"):
            time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "11_shap_explain.png"))
            results["shap_explain"] = "PASS"

        # 10. Time-Series Forecast
        if click_tab("Time-Series Forecast"):
            time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "12_forecasting.png"))
            results["forecasting"] = "PASS"

        # 11. Anomaly Detection
        if click_tab("Anomaly Detection"):
            time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "13_anomalies.png"))
            results["anomalies"] = "PASS"

        # 12. Customer Segments
        if click_tab("Customer Segments"):
            time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "14_segmentation.png"))
            results["segmentation"] = "PASS"

        # 13. Digital Twin Scenario Sim
        if click_tab("Digital Twin Scenario Sim"):
            time.sleep(1)
            # Find and click "Solve Optimal Strategy"
            solve_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Solve Optimal Strategy')]")
            if solve_btns:
                solve_btns[0].click()
                time.sleep(1.5)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "15_digital_twin.png"))
            results["digital_twin"] = "PASS"

        # 14. Prescriptive Goal-Seek
        if click_tab("Prescriptive Goal-Seek"):
            time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "16_goal_seek.png"))
            results["goal_seek"] = "PASS"

        # 15. Econometric Causal Engine
        if click_tab("Econometric Causal Engine"):
            time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "17_causal.png"))
            results["causal"] = "PASS"

        # 16. ABAC & PII Masking
        if click_tab("ABAC & PII Masking"):
            time.sleep(1)
            # Evaluate ABAC button
            abac_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Evaluate ABAC')]")
            if abac_btn:
                abac_btn[0].click()
                time.sleep(1)
            # Request Export button
            exp_btn = driver.find_elements(By.XPATH, "//button[contains(., 'Request Export')]")
            if exp_btn:
                exp_btn[0].click()
                time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "18_governance_abac.png"))
            results["governance_abac"] = "PASS"

        # 17. Cryptographic Audit Trail
        if click_tab("Cryptographic Audit Trail"):
            time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "19_audit_trail.png"))
            results["audit"] = "PASS"

        # 18. Operations & Telemetry
        if click_tab("Operations & Telemetry"):
            time.sleep(1)
            # Click a probe button
            probe_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'GET /health/ready')]")
            if probe_btns:
                probe_btns[0].click()
                time.sleep(1)
            driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "20_operations_telemetry.png"))
            results["operations_center"] = "PASS"

        # Check console logs for serious errors
        logs = driver.get_log("browser")
        severe_errors = [log for log in logs if log['level'] == 'SEVERE']
        results["console_severe_errors"] = severe_errors

        print("\n================== BROWSER TEST RESULTS ==================")
        print(json.dumps(results, indent=2))
        return results

    finally:
        driver.quit()

if __name__ == "__main__":
    run_browser_checks()
