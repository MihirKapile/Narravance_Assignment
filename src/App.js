import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Bar, Line } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

function App() {
    const [taskId, setTaskId] = useState(null);
    const [status, setStatus] = useState('');
    const [data, setData] = useState([]);
    const [metadata, setMetadata] = useState([]);
    const barChartRef = useRef(null);
    const lineChartRef = useRef(null);

    useEffect(() => {
        axios.get('http://127.0.0.1:5000/metadata')
            .then(response => setMetadata(response.data))
            .catch(error => console.error(error));
    }, []);

    const createTask = async () => {
        const response = await axios.post('http://127.0.0.1:5000/tasks', {
            filter_params: { make: ['TESLA', 'BMW'] }
        });
        setTaskId(response.data.task_id);
        setStatus(response.data.status);
    };

    const checkStatus = async () => {
        const response = await axios.get(`http://127.0.0.1:5000/tasks/${taskId}`);
        setStatus(response.data.status);
        
        if (response.data.status === 'completed') {
            fetchData();
        }
    };

    const fetchData = async () => {
        const response = await axios.get(`http://127.0.0.1:5000/data/${taskId}`);
        setData(response.data);
    };

    const barChartData = {
        labels: data.map(d => d.make),
        datasets: [
            {
                label: 'Electric Range',
                data: data.map(d => d.electric_range),
                backgroundColor: 'rgba(75,192,192,0.6)'
            }
        ]
    };

    const lineChartData = {
        labels: data.map(d => d.model_year),
        datasets: [
            {
                label: 'Base MSRP',
                data: data.map(d => d.base_msrp),
                borderColor: 'rgba(255,99,132,1)',
                fill: false
            }
        ]
    };

    // Function to destroy the chart instance
    const destroyChart = (chartRef) => {
        if (chartRef.current) {
            chartRef.current.destroy();
        }
    };

    return (
        <div>
            <h1>EV Analytics</h1>
            <button onClick={createTask}>Create Task</button>
            {taskId && <p>Task ID: {taskId}</p>}
            {status && <p>Status: {status}</p>}
            <button onClick={checkStatus}>Check Status</button>
            
            {data.length > 0 && (
                <div>
                    <h2>Electric Vehicle Analytics</h2>
                    
                    {/* Bar Chart */}
                    <div>
                        <h3>Electric Range by Make</h3>
                        {destroyChart(barChartRef)}
                        <Bar data={barChartData} ref={barChartRef} />
                    </div>
                    
                    {/* Line Chart */}
                    <div>
                        <h3>Base MSRP Over Model Year</h3>
                        {destroyChart(lineChartRef)}
                        <Line data={lineChartData} ref={lineChartRef} />
                    </div>
                </div>
            )}

            {metadata.length > 0 && (
                <div>
                    <h2>Dataset Metadata</h2>
                    <ul>
                        {metadata.map((col, index) => (
                            <li key={index}>
                                <strong>{col.name}</strong>: {col.description} (Type: {col.dataType})
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

export default App;