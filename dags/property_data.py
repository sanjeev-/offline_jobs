from airflow import DAG
from airflow.operators import BashOperator,PythonOperator
from datetime import datetime, timedelta

"""
Planned layout:

Remax_Scrape_Script -> Sensor -> Store Images on Google Cloud Storage -> Load Property Data Onto Buyer App
                              -> Load Property Data to ML DB
                              
"""

two_days_ago = datetime.combine(datetime.today() - timedelta(2),
                                      datetime.min.time())
default_args = {
        'owner': 'airflow',
        'depends_on_past': False,
        'start_date': two_days_ago,
        'email': ['sanjeev@ribbonhome.com'],
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
}

dag = DAG('property_data', default_args=default_args, schedule_interval='*/5 * * * *')

t0 = BashOperator(
    task_id = 'test',
    bash_command='echo foo > output.txt',
    dag=dag
)

t1 = BashOperator(
    task_id='switch_to_correct_directory',
    bash_command = 'cd p/jobs/property_data/ ',
    dag=dag
)

t2 = BashOperator(
    task_id='run_new_listings_from_remax',
    bash_command='python /Users/sanjeevsreetharan/Documents/ribbon/airflow/dags/jobs/property_data/utils/run_remax_new_listings.py --city charlotte --state nc ',
    dag=dag)

t0 >> t1 >> t2