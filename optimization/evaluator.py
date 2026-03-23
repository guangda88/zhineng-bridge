def evaluate_websocket_params(params):
    max_connections = params.get("max_connections", 10)
    ping_interval = params.get("ping_interval", 10)
    message_queue_size = params.get("message_queue_size", 100)
    
    score = (
        max_connections / 200 * 0.5 +
        (1 / ping_interval) / 0.2 * 0.3 +
        message_queue_size / 5000 * 0.2
    )
    return score

def evaluate_performance_params(params):
    output_update_interval = params.get("output_update_interval", 100)
    compression_enabled = params.get("compression_enabled", False)
    batch_size = params.get("batch_size", 100)
    
    score = (
        (1 / output_update_interval) / 0.01 * 0.3 +
        (1 if compression_enabled else 0) * 0.2 +
        batch_size / 1000 * 0.5
    )
    return score
