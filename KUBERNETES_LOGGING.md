# Kubernetes Logging Guide

This document explains how the EC2 Instance Controls application logging works in Kubernetes and provides best practices for log management.

## How Logging Works in Kubernetes

### **1. Container Logs**
When running in Kubernetes, all application logs go to:
- **stdout/stderr**: Container's standard output/error streams
- **Node filesystem**: Logs are stored on the node's filesystem
- **kubectl logs**: Accessible via `kubectl logs <pod-name>`

### **2. Log Collection**
Kubernetes automatically:
- Captures stdout/stderr from all containers
- Provides log rotation and retention
- Enables log access via kubectl

### **3. Multi-Pod Logging**
With multiple replicas, logs are distributed across pods:
```bash
# View logs from specific pod
kubectl logs ec2-instance-controls-abc123

# View logs from all pods in deployment
kubectl logs -l app=ec2-instance-controls

# Follow logs in real-time
kubectl logs -f -l app=ec2-instance-controls
```

## Log Structure in Kubernetes

### **Enhanced Metadata**
All logs now include Kubernetes-specific metadata:
```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "user_id": "U08QYU6AX0V",
  "action": "ec2_power_change",
  "target": "i-1234567890abcdef0",
  "status": "SUCCESS",
  "pod_name": "ec2-instance-controls-abc123",
  "namespace": "default",
  "deployment": "ec2-instance-controls"
}
```

### **Log Categories**
1. **REQUEST_AUDIT**: All HTTP requests
2. **AUDIT**: User actions and operations
3. **AWS_AUDIT**: AWS API calls
4. **SCHEDULE_AUDIT**: Schedule operations

## Logging Best Practices

### **1. Centralized Logging**
For production, implement centralized logging:

#### **Option A: ELK Stack**
```yaml
# Deploy Elasticsearch, Logstash, Kibana
# Configure Fluentd/Fluent Bit as log forwarder
```

#### **Option B: CloudWatch Logs (AWS)**
```yaml
# Use AWS CloudWatch Container Insights
# Configure log groups and streams
```

#### **Option C: Splunk**
```yaml
# Deploy Splunk Enterprise or Splunk Cloud
# Configure log forwarding
```

### **2. Log Aggregation with Fluentd**
Create a Fluentd DaemonSet to collect logs:

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
spec:
  selector:
    matchLabels:
      name: fluentd
  template:
    metadata:
      labels:
        name: fluentd
    spec:
      containers:
      - name: fluentd
        image: fluent/fluentd-kubernetes-daemonset:v1-debian-elasticsearch
        env:
        - name: FLUENT_ELASTICSEARCH_HOST
          value: "elasticsearch-service"
        - name: FLUENT_ELASTICSEARCH_PORT
          value: "9200"
        volumeMounts:
        - name: varlog
          mountPath: /var/log
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
```

### **3. Log Retention and Rotation**
Configure log retention policies:

```yaml
# In your deployment
spec:
  template:
    spec:
      containers:
      - name: ec2-control-app
        env:
        - name: LOG_RETENTION_DAYS
          value: "30"
```

## Monitoring and Alerting

### **1. Prometheus Metrics**
Add Prometheus metrics to the application:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
POWER_OPERATIONS = Counter('ec2_power_operations_total', 'EC2 power operations', ['operation', 'status'])

@app.route('/metrics')
def metrics():
    return generate_latest()
```

### **2. Grafana Dashboards**
Create dashboards for:
- Request rates and response times
- EC2 operation success/failure rates
- User activity patterns
- Error rates and types

### **3. Alerting Rules**
Set up alerts for:
- High error rates
- Failed EC2 operations
- Unusual user activity patterns
- Application health issues

## Log Analysis Commands

### **Basic Log Queries**
```bash
# View all logs from the deployment
kubectl logs -l app=ec2-instance-controls

# View logs from last hour
kubectl logs -l app=ec2-instance-controls --since=1h

# View logs with timestamps
kubectl logs -l app=ec2-instance-controls --timestamps

# View logs from specific pod
kubectl logs ec2-instance-controls-abc123
```

### **Advanced Log Filtering**
```bash
# Find all failed operations
kubectl logs -l app=ec2-instance-controls | grep '"status":"FAILED"'

# Find all actions by specific user
kubectl logs -l app=ec2-instance-controls | grep '"user_id":"U08QYU6AX0V"'

# Find all power state changes
kubectl logs -l app=ec2-instance-controls | grep '"action":"ec2_power_change"'

# Find all AWS operations
kubectl logs -l app=ec2-instance-controls | grep "AWS_AUDIT"
```

### **JSON Log Parsing**
```bash
# Extract specific fields using jq
kubectl logs -l app=ec2-instance-controls | jq -r '.user_id, .action, .status'

# Count operations by type
kubectl logs -l app=ec2-instance-controls | jq -r '.action' | sort | uniq -c

# Find recent errors
kubectl logs -l app=ec2-instance-controls --since=1h | jq 'select(.status == "FAILED")'
```

## Persistent Storage for Schedules

### **Volume Configuration**
The application uses persistent storage for schedules:

```yaml
# Persistent Volume for schedules
apiVersion: v1
kind: PersistentVolume
metadata:
  name: ec2-controls-pv
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteMany
  hostPath:
    path: /data/ec2-controls
```

### **Backup Strategy**
Implement regular backups of schedule data:

```bash
# Backup schedules
kubectl exec ec2-instance-controls-abc123 -- cat /app/schedules/schedules.json > schedules-backup.json

# Restore schedules
kubectl cp schedules-backup.json ec2-instance-controls-abc123:/app/schedules/schedules.json
```

## Security Considerations

### **1. Log Access Control**
- Restrict access to logs based on RBAC
- Use namespaces to isolate environments
- Implement log encryption at rest

### **2. Sensitive Data Handling**
- Logs are truncated to prevent sensitive data exposure
- AWS credentials are stored in Kubernetes secrets
- User tokens are not logged in full

### **3. Audit Compliance**
- All user actions are logged with timestamps
- Pod and namespace information is included
- Success/failure status is tracked

## Troubleshooting

### **Common Issues**

#### **1. Logs Not Appearing**
```bash
# Check if pods are running
kubectl get pods -l app=ec2-instance-controls

# Check pod logs
kubectl logs <pod-name>

# Check pod events
kubectl describe pod <pod-name>
```

#### **2. Schedule Data Loss**
```bash
# Check persistent volume status
kubectl get pv
kubectl get pvc

# Check volume mounts
kubectl exec <pod-name> -- ls -la /app/schedules/
```

#### **3. High Log Volume**
```bash
# Check log size
kubectl exec <pod-name> -- du -sh /var/log/

# Implement log rotation
kubectl exec <pod-name> -- logrotate -f /etc/logrotate.conf
```

## Production Recommendations

### **1. Log Aggregation**
- Deploy centralized logging solution (ELK, Splunk, etc.)
- Configure log forwarding from all pods
- Set up log retention policies

### **2. Monitoring**
- Deploy Prometheus and Grafana
- Set up alerting for critical issues
- Create dashboards for operational visibility

### **3. Backup and Recovery**
- Regular backups of schedule data
- Test recovery procedures
- Document disaster recovery plans

### **4. Security**
- Implement network policies
- Use service accounts with minimal permissions
- Regular security audits of logs 