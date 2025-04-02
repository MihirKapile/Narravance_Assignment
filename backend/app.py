from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import json
import time
from threading import Thread
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vehicles.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), default="pending")
    filter_params = db.Column(db.String(200))

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    vin = db.Column(db.String(20))
    county = db.Column(db.String(50))
    city = db.Column(db.String(50))
    state = db.Column(db.String(10))
    postal_code = db.Column(db.String(10))
    model_year = db.Column(db.Integer)
    make = db.Column(db.String(50))
    model = db.Column(db.String(50))
    ev_type = db.Column(db.String(50))
    electric_range = db.Column(db.Integer)
    base_msrp = db.Column(db.Float)

with app.app_context():
    db.create_all()
    
# Load JSON metadata
with open('metadata.json') as f:
    metadata = json.load(f)

# Simulated Job Queue
job_queue = []

def process_task(task_id):
    with app.app_context():
        # Simulate processing delay
        time.sleep(5)
        
        # Update task status to "in progress"
        task = Task.query.get(task_id)
        task.status = "in progress"
        db.session.commit()
        
        # Load CSV data and filter it (simulate external data sourcing)
        csv_data = pd.read_csv('vehicles.csv')
        
        # Example filtering logic (you can customize this)
        filtered_data = csv_data[csv_data['Make'].isin(['TESLA', 'BMW'])]
        
        # Save data to database
        for _, row in filtered_data.iterrows():
            vehicle = Vehicle(
                task_id=task_id,
                vin=row['VIN (1-10)'],
                county=row['County'],
                city=row['City'],
                state=row['State'],
                postal_code=row['Postal Code'],
                model_year=row['Model Year'],
                make=row['Make'],
                model=row['Model'],
                ev_type=row['Electric Vehicle Type'],
                electric_range=row['Electric Range'],
                base_msrp=row.get('Base MSRP', 0)
            )
            db.session.add(vehicle)
        
        db.session.commit()
        
        # Update task status to "completed"
        task.status = "completed"
        db.session.commit()

@app.route('/tasks', methods=['POST'])
def create_task():
    filter_params = request.json.get('filter_params', {})
    
    # Create a new task
    new_task = Task(filter_params=str(filter_params))
    db.session.add(new_task)
    db.session.commit()
    
    # Add task to job queue and process it in a separate thread
    job_queue.append(new_task.id)
    Thread(target=process_task, args=(new_task.id,)).start()
    
    return jsonify({"task_id": new_task.id, "status": new_task.status})

@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task_status(task_id):
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({"error": "Task not found"}), 404
    
    return jsonify({"task_id": task.id, "status": task.status})

@app.route('/data/<int:task_id>', methods=['GET'])
def get_task_data(task_id):
    vehicles = Vehicle.query.filter_by(task_id=task_id).all()
    
    if not vehicles:
        return jsonify({"error": "No data found for this task"}), 404
    
    result = [
        {
            "vin": v.vin,
            "county": v.county,
            "city": v.city,
            "state": v.state,
            "postal_code": v.postal_code,
            "model_year": v.model_year,
            "make": v.make,
            "model": v.model,
            "ev_type": v.ev_type,
            "electric_range": v.electric_range,
            "base_msrp": v.base_msrp
        }
        for v in vehicles
    ]
    
    return jsonify(result)

@app.route('/metadata', methods=['GET'])
def get_metadata():
    try:
        columns = metadata['meta']['view']['columns']
        column_info = [
            {
                "name": col['name'],
                "description": col.get('description', 'No description available'),
                "dataType": col['dataTypeName']
            }
            for col in columns if col.get('name')
        ]
        return jsonify(column_info)
    except KeyError as e:
        return jsonify({"error": f"KeyError: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)