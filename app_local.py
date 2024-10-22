from flask import Flask, render_template_string, request
import pandas as pd

app = Flask(__name__)

# Load Excel data from the local file
file_path = 'sizing.xlsx'

# Load the "CALCULATOR" sheet into memory
calculator_df = pd.read_excel(file_path, sheet_name='CALCULATOR')

# Helper function to calculate hardware requirements
def calculate_requirements(inputs):
    results = {
        'nodes': 0,
        'cpu_cores': 0,
        'ram_gb': 0,
        'storage_gb': 0,
        'nfs_gb': 0,
        'cdw_local_disk_gb': 0,
        'warnings': []
    }

    # Resource calculations for ECS Master/Server
    ecs_master_cpu = 32
    ecs_master_ram = 64
    ecs_master_os_disk = 1000
    ecs_master_longhorn_disk = 235

    # Resource calculations for ECS Worker/Agent
    ecs_worker_nodes = 14
    ecs_worker_cpu = 64
    ecs_worker_ram = 256
    ecs_worker_os_disk = 1000
    ecs_worker_longhorn_disk = 235
    ecs_worker_cdw_disk = 630

    # Add resources for Environment and Embedded Database
    results['nodes'] += inputs['environment']  # Add the specified number of environment nodes
    results['storage_gb'] += inputs['embedded_db']  # Add embedded database storage in GB

    # CDW: Data Catalog
    results['nodes'] += inputs['data_catalog']  # Each Data Catalog adds 1 node

    # CDW: Hive Virtual Warehouse
    results['nodes'] += inputs['hive_vw']  # Each Hive VW adds 1 node

    # CDW: Hive LITE Executor
    results['cpu_cores'] += inputs['hive_lite_exec'] * 2  # 2 CPU per Hive LITE Executor
    results['ram_gb'] += inputs['hive_lite_exec'] * 4    # 4 GB per Hive LITE Executor

    # CDW: Hive PROD Executor
    results['cpu_cores'] += inputs['hive_prod_exec'] * 8  # 8 CPU per Hive PROD Executor
    results['ram_gb'] += inputs['hive_prod_exec'] * 32    # 32 GB per Hive PROD Executor

    # CDW: Impala Virtual Warehouse
    results['nodes'] += inputs['impala_vw']  # Each Impala VW adds 1 node

    # CDW: Impala LITE Executor
    results['cpu_cores'] += inputs['impala_lite_exec'] * inputs['impala_lite_exec_cpu']
    results['ram_gb'] += inputs['impala_lite_exec'] * inputs['impala_lite_exec_mem']

    # CDW: Impala LITE Coordinator
    results['cpu_cores'] += inputs['impala_lite_coord_qty'] * inputs['impala_lite_coord_cpu']
    results['ram_gb'] += inputs['impala_lite_coord_qty'] * inputs['impala_lite_coord_mem']

    # CDW: Impala PROD Executor
    results['cpu_cores'] += inputs['impala_prod_exec'] * inputs['impala_prod_exec_cpu']
    results['ram_gb'] += inputs['impala_prod_exec'] * inputs['impala_prod_exec_mem']

    # CDW: Impala PROD Coordinator
    results['cpu_cores'] += inputs['impala_prod_coord_qty'] * inputs['impala_prod_coord_cpu']
    results['ram_gb'] += inputs['impala_prod_coord_qty'] * inputs['impala_prod_coord_mem']

    # CDW: Data Viz (Small, Medium, Large)
    results['cpu_cores'] += inputs['data_viz_small'] * 2  # 2 CPU per small Data Viz
    results['ram_gb'] += inputs['data_viz_small'] * 8     # 8 GB per small Data Viz

    results['cpu_cores'] += inputs['data_viz_medium'] * 4  # 4 CPU per medium Data Viz
    results['ram_gb'] += inputs['data_viz_medium'] * 16    # 16 GB per medium Data Viz

    results['cpu_cores'] += inputs['data_viz_large'] * 6  # 6 CPU per large Data Viz
    results['ram_gb'] += inputs['data_viz_large'] * 24    # 24 GB per large Data Viz

    # CDE: Service
    results['nodes'] += inputs['cde_service']  # Each CDE service adds 1 node

    # CDE: Virtual Cluster
    results['nodes'] += inputs['cde_vc']  # Each virtual cluster adds 1 node

    # CDE: Job Driver
    results['cpu_cores'] += inputs['job_quantity'] * inputs['job_driver_cpu']  # CPU per Job Driver
    results['ram_gb'] += inputs['job_quantity'] * inputs['job_driver_mem']     # RAM per Job Driver

    # CDE: Job Executor
    results['cpu_cores'] += inputs['job_exec'] * inputs['job_exec_cpu']  # CPU per Job Executor
    results['ram_gb'] += inputs['job_exec'] * inputs['job_exec_mem']     # RAM per Job Executor

    # Add ECS Master resources
    results['nodes'] += 1  # 1 master node
    results['cpu_cores'] += ecs_master_cpu
    results['ram_gb'] += ecs_master_ram
    results['storage_gb'] += ecs_master_os_disk + ecs_master_longhorn_disk

    # Add ECS Worker resources
    results['nodes'] += ecs_worker_nodes
    results['cpu_cores'] += ecs_worker_nodes * ecs_worker_cpu
    results['ram_gb'] += ecs_worker_nodes * ecs_worker_ram
    results['storage_gb'] += ecs_worker_nodes * (ecs_worker_os_disk + ecs_worker_longhorn_disk)
    results['cdw_local_disk_gb'] += ecs_worker_nodes * ecs_worker_cdw_disk

    # CML: Workspace
    results['nodes'] += inputs['cml_workspace']  # Each workspace adds 1 node

    # CML: XSmall Session (2 CPU, 4 GB)
    results['cpu_cores'] += inputs['cml_xsmall_session'] * 2  # 2 CPU per XSmall session
    results['ram_gb'] += inputs['cml_xsmall_session'] * 4     # 4 GB per XSmall session

    # CML: Small Session (4 CPU, 8 GB)
    results['cpu_cores'] += inputs['cml_small_session'] * 4  # 4 CPU per small session
    results['ram_gb'] += inputs['cml_small_session'] * 8    # 8 GB per small session

    # CML: Medium Session (6 CPU, 16 GB)
    results['cpu_cores'] += inputs['cml_medium_session'] * 6  # 6 CPU per medium session
    results['ram_gb'] += inputs['cml_medium_session'] * 16    # 16 GB per medium session

    # CML: Backup Workspace
    if inputs['backup_workspace'] > 0:
        results['nodes'] += inputs['backup_workspace']  # Each backup workspace adds 1 node

    # CML: Model Registry
    if inputs['model_registry']:
        results['nodes'] += 1  # Model Registry adds 1 node


    # Check if Internal NFS is used
    if inputs['internal_nfs']:
        results['nfs_gb'] += inputs['cml_nfs']
    else:
        results['nfs_gb'] = 0  # No contribution from internal NFS if external is used

    # DRS: Control Plane Backup
    if inputs['drs_backup'] > 0:
        results['nodes'] += inputs['drs_backup']  # Each control plane backup adds 1 node


    # Add additional OCP Worker resources
    ocp_worker_nodes = 30
    ocp_worker_cpu = 32
    ocp_worker_ram = 128

    results['nodes'] += ocp_worker_nodes
    results['cpu_cores'] += ocp_worker_nodes * ocp_worker_cpu
    results['ram_gb'] += ocp_worker_nodes * ocp_worker_ram

    # Add CCU total resources
    results['ccu_cpu'] = results['cpu_cores'] + 928  # ECS baseline CPU
    results['ccu_ram'] = results['ram_gb'] + 3648    # ECS baseline RAM

    # Add OCP CCU total resources
    results['ccu_cpu'] += 960  # OCP CPU
    results['ccu_ram'] += 3840  # OCP RAM

    return results
# Define the results template as a global variable
# Create results page with Hardware Dimensioning Output format in one block
result_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sizing Results</title>
    <style>
        /* General Body Styling */
        body {
            background-color: #f4f4f4;
            font-family: Arial, sans-serif;
            color: #333;
        }

        .container {
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background-color: #ffffff;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }

        h1, h2 {
            color: #005a8b;
        }

        h1 {
            font-size: 28px;
            border-bottom: 2px solid #005a8b;
            padding-bottom: 8px;
        }

        h2 {
            font-size: 24px;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        .results-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }

        .results-table th, .results-table td {
            border: 1px solid #ccc;
            padding: 8px;
            text-align: center;
        }

        .results-table th {
            background-color: #005a8b;
            color: white;
            font-weight: bold;
        }

        .results-table .header {
            background-color: #e0e0e0;  /* Gray background for section headers */
            font-weight: bold;
            text-align: left;
        }

        .results-table .gray {
            background-color: #e0e0e0;  /* Gray for external NFS rows */
        }

        .results-table .highlight {
            background-color: #f0e68c;  /* Highlight for important values */
        }

        .results-table .yellow {
            background-color: #fffdd0;  /* Light yellow background for cells */
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Sizing Results</h1>

        <h2>Hardware Dimensioning Output:</h2>
        <table class="results-table">
            <!-- Table Header -->
            <tr>
                <th>ECS</th>
                <th>Nodes</th>
                <th>Resource</th>
                <th>Value</th>
                <th>Metric</th>
                <th>Remark</th>
            </tr>

            <!-- Master/Server Section -->
            <tr class="header">
                <td rowspan="4">Master/Server</td>
                <td rowspan="4" class="highlight">1</td>
                <td>CPU cores</td>
                <td class="yellow">32</td>
                <td></td>
                <td>Each node.</td>
            </tr>
            <tr>
                <td>RAM</td>
                <td class="yellow">64</td>
                <td>GB</td>
                <td>Each node.</td>
            </tr>
            <tr>
                <td>OS Disk</td>
                <td class="yellow">1000</td>
                <td>GB</td>
                <td>Each node. SSD/NVMe is required. If RAID 1, deploy 2 disks.</td>
            </tr>
            <tr>
                <td>Longhorn Disk</td>
                <td class="yellow">235</td>
                <td>GB</td>
                <td>Each node. SSD/NVMe is recommended.</td>
            </tr>

            <!-- Worker/Agent Section -->
            <tr class="header">
                <td rowspan="5">Worker/Agent</td>
                <td rowspan="5" class="highlight">14</td>
                <td>CPU cores</td>
                <td class="yellow">64</td>
                <td></td>
                <td>Each node.</td>
            </tr>
            <tr>
                <td>RAM</td>
                <td class="yellow">256</td>
                <td>GB</td>
                <td>Each node.</td>
            </tr>
            <tr>
                <td>OS Disk</td>
                <td class="yellow">1000</td>
                <td>GB</td>
                <td>Each node. SSD/NVMe is recommended. If RAID 1, deploy 2 disks.</td>
            </tr>
            <tr>
                <td>Longhorn Disk</td>
                <td class="yellow">235</td>
                <td>GB</td>
                <td>Each node. SSD/NVMe is recommended. Use Logical Volume Manager (LVM).</td>
            </tr>
            <tr>
                <td>CDW Local Disk</td>
                <td class="yellow">630</td>
                <td>GB</td>
                <td>Each node. SSD/NVMe is recommended. Use Logical Volume Manager (LVM).</td>
            </tr>

            <!-- External NFS -->
            <tr class="gray">
                <td>External NFS</td>
                <td></td>
                <td></td>
                <td>{{ cml_nfs }}</td>
                <td>GB</td>
                <td>CML only. Minimum size.</td>
            </tr>

            <!-- Openshift 4 Worker Section -->
            <tr class="header">
                <td rowspan="3">Openshift 4 Worker</td>
                <td rowspan="3" class="highlight">30</td>
                <td>CPU cores</td>
                <td class="yellow">32</td>
                <td></td>
                <td>Each node.</td>
            </tr>
            <tr>
                <td>RAM</td>
                <td class="yellow">128</td>
                <td>GB</td>
                <td>Each node.</td>
            </tr>
            <tr>
                <td>CDW 630GB Disk</td>
                <td class="yellow">1</td>
                <td>unit</td>
                <td>Each node. SSD/NVMe is required.</td>
            </tr>

            <!-- OCS/ODF -->
            <tr class="gray">
                <td>OCS/ODF</td>
                <td></td>
                <td></td>
                <td>1525</td>
                <td>GB</td>
                <td>Usable Capacity (before applying replication).</td>
            </tr>

            <!-- CCU Section -->
            <tr class="header">
                <td colspan="2">CCU:</td>
                <td>Total</td>
                <td>CPU</td>
                <td>Memory</td>
                <td></td>
            </tr>
            <tr>
                <td colspan="2">ECS</td>
                <td></td>
                <td class="yellow">{{ results['ccu_cpu'] }}</td>
                <td class="yellow">{{ results['ccu_ram'] }}</td>
                <td></td>
            </tr>
            <tr>
                <td colspan="2">OCP</td>
                <td></td>
                <td class="yellow">960</td>
                <td class="yellow">3840</td>
                <td></td>
            </tr>
        </table>
    </div>


    {% if results['warnings'] %}
        <div class="warnings">
            <h3>Warnings:</h3>
            {% for warning in results['warnings'] %}
                <p class="orange">{{ warning }}</p>
            {% endfor %}
        </div>
    {% endif %}
    <br>
    <a href="/">Back to Calculator</a>
</body>
</html>
'''

@app.route('/')
def index():
    # Expanded input form with detailed CDW, CDE, and CML components
    from flask import Flask, render_template_string, request

    app = Flask(__name__)

    # Updated template with Cloudera styling
    html_content = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dynamic Sizing Calculator</title>
        <style>
            /* General Body Styling */
            body {
                background-color: #f4f4f4;  /* Light grey background */
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                color: #333;  /* Darker grey text */
            }

            /* Container for content */
            .container {
                max-width: 1200px;
                margin: 20px auto;
                padding: 20px;
                background-color: #ffffff;  /* White background for content */
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);  /* Soft shadow */
                border-radius: 8px;
            }

            /* Header Styling */
            h1, h2 {
                color: #005a8b;  /* Cloudera dark blue */
            }

            h1 {
                font-size: 28px;
                border-bottom: 2px solid #005a8b;
                padding-bottom: 8px;
            }

            h2 {
                font-size: 24px;
                margin-top: 20px;
                margin-bottom: 10px;
            }

            /* Input form styling */
            label {
                font-weight: bold;
                display: block;
                margin-bottom: 5px;
                margin-top: 10px;
                color: #005a8b;  /* Cloudera blue */
            }

            input[type="number"],
            input[type="text"],
            select {
                width: 100%;
                padding: 8px;
                margin-bottom: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
                box-sizing: border-box;
                font-size: 16px;
            }

            input[type="checkbox"] {
                margin-right: 5px;
            }

            input[type="submit"] {
                background-color: #005a8b;  /* Cloudera dark blue */
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }

            input[type="submit"]:hover {
                background-color: #00436a;  /* Darker blue on hover */
            }

            .yellow {
                background-color: #fffdd0;  /* Light yellow background */
            }

            .green {
                background-color: #d4edda;  /* Light green background */
            }

            .error {
                color: red;
                margin-top: 10px;
            }

            .output {
                margin-top: 20px;
                font-weight: bold;
            }

            .results-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }

            .results-table th, .results-table td {
                border: 1px solid #ccc;
                padding: 10px;
                text-align: left;
            }

            .results-table th {
                background-color: #005a8b;  /* Cloudera dark blue */
                color: white;
            }

            .results-table td {
                background-color: #f4f4f4;  /* Light grey for rows */
            }

            a {
                color: #005a8b;  /* Cloudera dark blue */
                text-decoration: none;
            }

            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Dynamic Sizing Calculator</h1>
            <form action="/calculate" method="post">
                <!-- Add other inputs here -->
                <!-- CDW Inputs with Validations -->
                             <!-- Environment Inputs -->
                             <h2>Environment Inputs</h2>
                             <label for="environment">Environment (Min: 1):</label>
                             <input type="number" name="environment" min="1" value="1" class="green" required><br><br>

                             <label for="embedded_db">Embedded Database (GB, Recommend: 200):</label>
                             <input type="number" name="embedded_db" min="0" value="200" class="yellow" required><br><br>


                            <!-- CDW Inputs -->
                            <h2>CDW Inputs</h2>

                            <!-- Data Catalog -->
                            <label for="data_catalog">Data Catalog (Min: 1):</label>
                            <input type="number" name="data_catalog" min="1" class="green" value="1" required><br><br>

                            <!-- Hive Virtual Warehouse -->
                            <label for="hive_vw">Hive Virtual Warehouse (Min: 1):</label>
                            <input type="number" name="hive_vw" min="1" class="yellow" value="1" required><br><br>

                            <!-- Hive LITE Executor -->
                            <label for="hive_lite_exec">Hive LITE Executor (Min: 1):</label>
                            <input type="number" name="hive_lite_exec" min="1" class="yellow" value="1" required><br><br>

                            <!-- Hive PROD Executor -->
                            <label for="hive_prod_exec">Hive PROD Executor (Min: 1):</label>
                            <input type="number" name="hive_prod_exec" min="1" class="yellow" value="1" required><br><br>

                            <!-- Impala Virtual Warehouse -->
                            <label for="impala_vw">Impala Virtual Warehouse (Min: 1):</label>
                            <input type="number" name="impala_vw" min="1" class="green" value="1" required><br><br>

                            <!-- Impala LITE Executor -->
                            <label for="impala_lite_exec">Impala LITE Executor (Min: 1):</label>
                            <input type="number" name="impala_lite_exec" min="1" class="yellow" value="1" required><br><br>

                            <label for="impala_lite_exec_cpu">Impala LITE Executor CPU cores (Default: 3):</label>
                            <input type="number" name="impala_lite_exec_cpu" min="1" class="yellow" value="3"><br><br>

                            <label for="impala_lite_exec_mem">Impala LITE Executor Mem (GB, Default: 25):</label>
                            <input type="number" name="impala_lite_exec_mem" min="25" class="yellow" value="25"><br><br>

                            <!-- Impala LITE Coordinator -->
                            <label for="impala_lite_coord_qty">Impala LITE Coordinator Quantity (Default: 2):</label>
                            <input type="number" name="impala_lite_coord_qty" min="1" class="yellow" value="2"><br><br>

                            <label for="impala_lite_coord_cpu">Impala LITE Coordinator CPU cores (Default: 1):</label>
                            <input type="number" name="impala_lite_coord_cpu" min="1" class="yellow" value="1"><br><br>

                            <label for="impala_lite_coord_mem">Impala LITE Coordinator Mem (GB, Default: 25):</label>
                            <input type="number" name="impala_lite_coord_mem" min="25" class="yellow" value="25"><br><br>

                            <!-- Impala PROD Executor Inputs -->
                            <h2>Impala PROD Executor Inputs</h2>

                            <label for="impala_prod_exec">Impala PROD Executor (Min: 1):</label>
                            <input type="number" name="impala_prod_exec" min="1" class="yellow" value="1" required><br><br>

                            <label for="impala_prod_exec_cpu">Impala PROD Executor CPU cores (Default: 14):</label>
                            <input type="number" name="impala_prod_exec_cpu" min="1" class="yellow" value="14" required><br><br>

                            <label for="impala_prod_exec_mem">Impala PROD Executor Mem (GB, Default: 128):</label>
                            <input type="number" name="impala_prod_exec_mem" min="128" class="yellow" value="128" required><br><br>

                            <!-- Impala PROD Coordinator Inputs -->
                            <h2>Impala PROD Coordinator Inputs</h2>

                            <label for="impala_prod_coord_qty">Impala PROD Coordinator (Quantity, Default: 2):</label>
                            <input type="number" name="impala_prod_coord_qty" min="1" class="yellow" value="2" required><br><br>

                            <label for="impala_prod_coord_cpu">Impala PROD Coordinator CPU cores (Default: 14):</label>
                            <input type="number" name="impala_prod_coord_cpu" min="1" class="yellow" value="14" required><br><br>

                            <label for="impala_prod_coord_mem">Impala PROD Coordinator Mem (GB, Default: 128):</label>
                            <input type="number" name="impala_prod_coord_mem" min="128" class="yellow" value="128" required><br><br>

                            <!-- Data Viz Inputs -->
                            <h2>Data Viz Inputs</h2>

                            <label for="data_viz_small">Data Viz (small) 2 CPU, 8GB (Min: 1):</label>
                            <input type="number" name="data_viz_small" min="1" class="green" value="1" required><br><br>

                            <label for="data_viz_medium">Data Viz (medium) 4 CPU, 16GB (Min: 1):</label>
                            <input type="number" name="data_viz_medium" min="1" class="green" value="1" required><br><br>

                            <label for="data_viz_large">Data Viz (large) 6 CPU, 24GB (Min: 1):</label>
                            <input type="number" name="data_viz_large" min="1" class="green" value="1" required><br><br>

                           <!-- CDE Inputs -->
                           <h2>CDE Inputs</h2>

                           <label for="cde_service">CDE Service (Min: 1):</label>
                           <input type="number" name="cde_service" min="1" class="green" value="1" required><br><br>

                           <label for="cde_vc">Virtual Cluster (Min: 1):</label>
                           <input type="number" name="cde_vc" min="1" class="green" value="1" required><br><br>

                           <label for="job_quantity">Quantity of Job(s) (Min: 1):</label>
                           <input type="number" name="job_quantity" min="1" class="green" value="7" required><br><br>

                           <label for="job_exec">Quantity of Executor(s) (Min: 1):</label>
                           <input type="number" name="job_exec" min="1" class="green" value="2" required><br><br>

                           <label for="job_driver_cpu">Job Driver CPU (Min: 1):</label>
                           <input type="number" name="job_driver_cpu" min="1" class="green" value="2" required><br><br>

                           <label for="job_driver_mem">Job Driver Mem (GB, Min: 1):</label>
                           <input type="number" name="job_driver_mem" min="1" class="green" value="4" required><br><br>

                           <label for="job_exec_cpu">Job Executor CPU (Min: 1):</label>
                           <input type="number" name="job_exec_cpu" min="1" class="green" value="2" required><br><br>

                           <label for="job_exec_mem">Job Executor Mem (GB, Min: 1):</label>
                           <input type="number" name="job_exec_mem" min="1" class="green" value="20" required><br><br>

                            <!-- CML Inputs with Validations -->
                            <h2>CML Inputs</h2>
                            <label for="cml_workspace">Workspace (Min: 1):</label>
                            <input type="number" name="cml_workspace" min="1" class="green" value="1" required><br><br>

                            <label for="cml_xsmall_session">XSmall Session (2 CPU, 4 GB, Min: 1):</label>
                            <input type="number" name="cml_xsmall_session" min="1" class="yellow" value="2" required><br><br>

                            <label for="cml_small_session">Small Session (4 CPU, 8 GB, Min: 1):</label>
                            <input type="number" name="cml_small_session" min="1" class="yellow" value="2" required><br><br>

                            <label for="cml_medium_session">Medium Session (6 CPU, 16 GB, Min: 1):</label>
                            <input type="number" name="cml_medium_session" min="1" class="yellow" value="3" required><br><br>

                            <label for="cml_nfs">NFS (GB, Min: 100):</label>
                            <input type="number" name="cml_nfs" min="100" class="yellow" value="100" required><br><br>

                            <label for="internal_nfs">Use Internal NFS:</label>
                            <input type="checkbox" name="internal_nfs" value="on"><br><br>

                            <label for="backup_workspace">Backup Workspace (Quantity, Min: 0):</label>
                            <input type="number" name="backup_workspace" min="0" class="yellow" value="0" required><br><br>

                            <label for="model_registry">Model Registry (Tick to use):</label>
                            <input type="checkbox" name="model_registry"><br><br>

                            <!-- DRS Inputs -->
                            <h2>DRS Backup</h2>

                            <label for="drs_backup">Number of Control Plane Backup(s) (Min: 0):</label>
                            <input type="number" name="drs_backup" min="0" class="yellow" value="0" required><br><br>


                            <!-- Hardware Specifications -->
                            <h3>Hardware Specifications</h3>
                            <label for="max_cpu_per_node">Max CPU per Node:</label>
                            <input type="number" name="max_cpu_per_node" min="1" value="32" required><br><br>

                            <label for="max_ram_per_node">Max RAM (GB) per Node:</label>
                            <input type="number" name="max_ram_per_node" min="1" value="128" required><br><br>

                            <label for="max_storage_per_node">Max Storage (GB) per Node:</label>
                            <input type="number" name="max_storage_per_node" min="1" value="2000" required><br><br>
                <input type="submit" value="Calculate">
            </form>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_content)
@app.route('/calculate', methods=['POST'])
def calculate():
    # Collect user inputs
    inputs = {
        'environment': int(request.form.get('environment', 1)),
        'embedded_db': int(request.form.get('embedded_db', 200)),
        'data_catalog': int(request.form.get('data_catalog', 1)),
        'hive_vw': int(request.form.get('hive_vw', 1)),
        'hive_lite_exec': int(request.form.get('hive_lite_exec', 1)),
        'hive_prod_exec': int(request.form.get('hive_prod_exec', 1)),
        'impala_vw': int(request.form.get('impala_vw', 1)),
        'impala_lite_exec': int(request.form.get('impala_lite_exec', 1)),
        'impala_lite_exec_cpu': int(request.form.get('impala_lite_exec_cpu', 3)),
        'impala_lite_exec_mem': int(request.form.get('impala_lite_exec_mem', 25)),
        'impala_lite_coord_qty': int(request.form.get('impala_lite_coord_qty', 2)),
        'impala_lite_coord_cpu': int(request.form.get('impala_lite_coord_cpu', 1)),
        'impala_lite_coord_mem': int(request.form.get('impala_lite_coord_mem', 25)),
        'impala_prod_exec': int(request.form.get('impala_prod_exec', 1)),
        'impala_prod_exec_cpu': int(request.form.get('impala_prod_exec_cpu', 14)),
        'impala_prod_exec_mem': int(request.form.get('impala_prod_exec_mem', 128)),
        'impala_prod_coord_qty': int(request.form.get('impala_prod_coord_qty', 2)),
        'impala_prod_coord_cpu': int(request.form.get('impala_prod_coord_cpu', 14)),
        'impala_prod_coord_mem': int(request.form.get('impala_prod_coord_mem', 128)),
        'data_viz_small': int(request.form.get('data_viz_small', 1)),
        'data_viz_medium': int(request.form.get('data_viz_medium', 1)),
        'data_viz_large': int(request.form.get('data_viz_large', 1)),
        'cde_service': int(request.form.get('cde_service', 1)),
        'cde_vc': int(request.form.get('cde_vc', 1)),
        'job_quantity': int(request.form.get('job_quantity', 1)),
        'job_exec': int(request.form.get('job_exec', 1)),
        'job_driver_cpu': int(request.form.get('job_driver_cpu', 2)),
        'job_driver_mem': int(request.form.get('job_driver_mem', 4)),
        'job_exec_cpu': int(request.form.get('job_exec_cpu', 2)),
        'job_exec_mem': int(request.form.get('job_exec_mem', 20)),
        'cml_workspace': int(request.form.get('cml_workspace', 1)),
        'cml_xsmall_session': int(request.form.get('cml_xsmall_session', 2)),
        'cml_small_session': int(request.form.get('cml_small_session', 2)),
        'cml_medium_session': int(request.form.get('cml_medium_session', 3)),
        'cml_nfs': int(request.form.get('cml_nfs', 100)),
        'internal_nfs': request.form.get('internal_nfs') == 'on',
        'backup_workspace': int(request.form.get('backup_workspace', 0)),
        'model_registry': request.form.get('model_registry') == 'on',
        'drs_backup': int(request.form.get('drs_backup', 0))
    }


    # Calculate requirements
    results = calculate_requirements(inputs)
    return render_template_string(result_template, inputs=inputs, results=results)
if __name__ == '__main__':
    # Use host='127.0.0.1' for local development
    app.run(host='127.0.0.1', port=5000, debug=True)

