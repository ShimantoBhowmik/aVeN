use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use tracing::info;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GuardrailMetrics {
    pub total_queries: u64,
    pub blocked_queries: u64,
    pub violations_by_type: HashMap<String, u64>,
}

impl Default for GuardrailMetrics {
    fn default() -> Self {
        Self {
            total_queries: 0,
            blocked_queries: 0,
            violations_by_type: HashMap::new(),
        }
    }
}

#[derive(Clone)]
pub struct GuardrailMetricsCollector {
    metrics: Arc<Mutex<GuardrailMetrics>>,
}

impl GuardrailMetricsCollector {
    pub fn new() -> Self {
        Self {
            metrics: Arc::new(Mutex::new(GuardrailMetrics::default())),
        }
    }

    pub fn record_query(&self) {
        if let Ok(mut metrics) = self.metrics.lock() {
            metrics.total_queries += 1;
        }
    }

    pub fn record_violation(&self, violation_type: &str) {
        if let Ok(mut metrics) = self.metrics.lock() {
            metrics.blocked_queries += 1;
            *metrics.violations_by_type.entry(violation_type.to_string()).or_insert(0) += 1;
        }
        
        info!("Guardrail violation recorded: {}", violation_type);
    }

    pub fn get_metrics(&self) -> GuardrailMetrics {
        match self.metrics.lock() {
            Ok(metrics) => metrics.clone(),
            Err(_) => {
                // In case of poisoned mutex, return default metrics
                GuardrailMetrics::default()
            }
        }
    }

    pub fn get_metrics_summary(&self) -> String {
        let metrics = self.get_metrics();
        let block_rate = if metrics.total_queries > 0 {
            (metrics.blocked_queries as f64 / metrics.total_queries as f64) * 100.0
        } else {
            0.0
        };

        format!(
            "Total Queries: {}, Blocked: {} ({:.2}%), Violation Types: {:?}",
            metrics.total_queries,
            metrics.blocked_queries,
            block_rate,
            metrics.violations_by_type
        )
    }
}

impl Default for GuardrailMetricsCollector {
    fn default() -> Self {
        Self::new()
    }
}
