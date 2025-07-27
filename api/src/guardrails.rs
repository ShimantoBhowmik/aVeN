use anyhow::{anyhow, Result};
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use tracing::warn;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum GuardrailViolation {
    PersonalData(String),
    FinancialAdvice(String),
    LegalAdvice(String),
    Toxicity(String),
    Fraud(String),
    OffTopic(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GuardrailResponse {
    pub blocked: bool,
    pub violation: Option<GuardrailViolation>,
    pub safe_response: Option<String>,
}

pub struct GuardrailEngine {
    personal_data_patterns: Vec<Regex>,
    financial_advice_keywords: HashSet<String>,
    legal_advice_keywords: HashSet<String>,
    toxic_patterns: Vec<Regex>,
    fraud_keywords: HashSet<String>,
    off_topic_keywords: HashSet<String>,
}

impl GuardrailEngine {
    pub fn new() -> Result<Self> {
        let personal_data_patterns = vec![
            // SSN patterns
            Regex::new(r"\b\d{3}-?\d{2}-?\d{4}\b")?,
            // Phone numbers
            Regex::new(r"\b\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})\b")?,
            // Email addresses
            Regex::new(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")?,
            // Credit card patterns (simplified)
            Regex::new(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")?,
            // Account numbers (8+ digits)
            Regex::new(r"\b\d{8,}\b")?,
            // Addresses (basic pattern)
            Regex::new(r"\b\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|boulevard|blvd|way|court|ct|place|pl)\b")?,
        ];

        let financial_advice_keywords = [
            "should i invest", "investment advice", "what should i do with my money",
            "financial planning", "retirement advice", "tax advice", "should i buy",
            "should i sell", "portfolio recommendation", "investment strategy",
            "financial recommendation", "money advice", "wealth management",
            "asset allocation", "risk tolerance", "investment options",
        ].iter().map(|s| s.to_lowercase()).collect();

        let legal_advice_keywords = [
            "legal advice", "what does the law say", "is this legal", "can i sue",
            "lawsuit", "attorney", "lawyer", "legal interpretation", "contract law",
            "my rights", "legal obligation", "violation of law", "court",
            "litigation", "legal action", "legal consequences", "compliance",
        ].iter().map(|s| s.to_lowercase()).collect();

        let toxic_patterns = vec![
            // Profanity and abuse (basic patterns - extend as needed)
            Regex::new(r"(?i)\b(fuck|shit|damn|bitch|asshole|idiot|stupid|moron)\b")?,
            // Threats
            Regex::new(r"(?i)\b(kill|hurt|harm|destroy|attack)\s+(you|aven)")?,
            // Harassment
            Regex::new(r"(?i)\b(hate|despise|loathe)\s+(you|this|aven)")?,
        ];

        let fraud_keywords = [
            "i am an aven employee", "i work for aven", "this is aven calling",
            "verify your account", "confirm your password", "account suspended",
            "urgent security alert", "click this link", "wire transfer",
            "send money", "gift cards", "bitcoin", "cryptocurrency payment",
            "internal aven information", "company secrets", "employee access",
        ].iter().map(|s| s.to_lowercase()).collect();

        let off_topic_keywords = [
            "politics", "election", "president", "democrat", "republican",
            "dating", "relationship", "marriage", "divorce", "sex",
            "religion", "god", "jesus", "islam", "buddhism", "christianity",
            "weather", "sports", "movie", "celebrity", "entertainment",
            "cooking", "recipe", "travel", "vacation", "health advice",
            "medical advice", "diagnosis", "medication", "treatment",
        ].iter().map(|s| s.to_lowercase()).collect();

        Ok(Self {
            personal_data_patterns,
            financial_advice_keywords,
            legal_advice_keywords,
            toxic_patterns,
            fraud_keywords,
            off_topic_keywords,
        })
    }

    pub fn check_input_guardrails(&self, input: &str) -> GuardrailResponse {
        let input_lower = input.to_lowercase();

        // Check for personal data
        if let Some(violation) = self.check_personal_data(input) {
            warn!("Personal data detected in input: {}", input);
            return GuardrailResponse {
                blocked: true,
                violation: Some(GuardrailViolation::PersonalData(violation)),
                safe_response: Some("For your security, please don't share personal information in this chat. Contact our secure customer service at support@aven.com or call our customer service line for account-specific inquiries.".to_string()),
            };
        }

        // Check for financial advice requests
        if self.contains_keywords(&input_lower, &self.financial_advice_keywords) {
            return GuardrailResponse {
                blocked: true,
                violation: Some(GuardrailViolation::FinancialAdvice("Financial advice request detected".to_string())),
                safe_response: Some("I can provide general information about Aven's products, but for personalized financial advice, please speak with a qualified Aven representative at support@aven.com or call our customer service line.".to_string()),
            };
        }

        // Check for legal advice requests
        if self.contains_keywords(&input_lower, &self.legal_advice_keywords) {
            return GuardrailResponse {
                blocked: true,
                violation: Some(GuardrailViolation::LegalAdvice("Legal advice request detected".to_string())),
                safe_response: Some("I cannot provide legal advice. For legal questions related to Aven's products or services, please consult with a qualified attorney or contact Aven's legal team through support@aven.com.".to_string()),
            };
        }

        // Check for toxicity
        if let Some(violation) = self.check_toxicity(input) {
            warn!("Toxic content detected in input: {}", input);
            return GuardrailResponse {
                blocked: true,
                violation: Some(GuardrailViolation::Toxicity(violation)),
                safe_response: Some("I'm here to help with questions about Aven's products and services. Let's keep our conversation professional and focused on how I can assist you.".to_string()),
            };
        }

        // Check for fraud attempts
        if self.contains_keywords(&input_lower, &self.fraud_keywords) {
            warn!("Potential fraud attempt detected: {}", input);
            return GuardrailResponse {
                blocked: true,
                violation: Some(GuardrailViolation::Fraud("Potential fraud attempt detected".to_string())),
                safe_response: Some("Aven employees will never ask for sensitive information through this chat. If you believe this is a legitimate Aven communication, please verify by calling our official customer service line.".to_string()),
            };
        }

        // Check for off-topic requests
        if self.contains_keywords(&input_lower, &self.off_topic_keywords) {
            return GuardrailResponse {
                blocked: true,
                violation: Some(GuardrailViolation::OffTopic("Off-topic request detected".to_string())),
                safe_response: Some("I'm designed to help with questions about Aven's products and services. For other topics, you might want to try a general-purpose AI assistant. How can I help you with Aven today?".to_string()),
            };
        }

        GuardrailResponse {
            blocked: false,
            violation: None,
            safe_response: None,
        }
    }

    pub fn check_output_guardrails(&self, output: &str) -> GuardrailResponse {
        // Check if the output accidentally contains personal data patterns
        if let Some(violation) = self.check_personal_data(output) {
            warn!("Personal data detected in output: {}", violation);
            return GuardrailResponse {
                blocked: true,
                violation: Some(GuardrailViolation::PersonalData(violation)),
                safe_response: Some("I apologize, but I cannot provide that information. For security reasons, please contact support@aven.com for assistance with account-specific matters.".to_string()),
            };
        }

        // Check if output seems to provide financial advice
        let output_lower = output.to_lowercase();
        let financial_advice_indicators = [
            "you should invest", "i recommend", "you should buy", "you should sell",
            "my advice is", "i suggest you", "the best option for you",
        ];

        if self.contains_keywords(&output_lower, &financial_advice_indicators.iter().map(|s| s.to_string()).collect()) {
            return GuardrailResponse {
                blocked: true,
                violation: Some(GuardrailViolation::FinancialAdvice("Output contains financial advice".to_string())),
                safe_response: Some("I can provide general information about Aven's products, but for personalized financial advice, please speak with a qualified Aven representative at support@aven.com.".to_string()),
            };
        }

        GuardrailResponse {
            blocked: false,
            violation: None,
            safe_response: None,
        }
    }

    fn check_personal_data(&self, text: &str) -> Option<String> {
        for pattern in &self.personal_data_patterns {
            if let Some(matches) = pattern.find(text) {
                return Some(format!("Personal data pattern detected: {}", matches.as_str()));
            }
        }
        None
    }

    fn check_toxicity(&self, text: &str) -> Option<String> {
        for pattern in &self.toxic_patterns {
            if let Some(matches) = pattern.find(text) {
                return Some(format!("Toxic content detected: {}", matches.as_str()));
            }
        }
        None
    }

    fn contains_keywords(&self, text: &str, keywords: &HashSet<String>) -> bool {
        keywords.iter().any(|keyword| text.contains(keyword))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_personal_data_detection() {
        let engine = GuardrailEngine::new().unwrap();
        
        let test_cases = vec![
            "My SSN is 123-45-6789",
            "Call me at 555-123-4567",
            "Email me at test@example.com",
            "My account number is 12345678",
        ];

        for case in test_cases {
            let result = engine.check_input_guardrails(case);
            assert!(result.blocked, "Should block: {}", case);
        }
    }

    #[test]
    fn test_financial_advice_detection() {
        let engine = GuardrailEngine::new().unwrap();
        
        let test_cases = vec![
            "Should I invest in stocks?",
            "What investment advice do you have?",
            "Tell me about financial planning",
        ];

        for case in test_cases {
            let result = engine.check_input_guardrails(case);
            assert!(result.blocked, "Should block: {}", case);
        }
    }

    #[test]
    fn test_safe_queries() {
        let engine = GuardrailEngine::new().unwrap();
        
        let test_cases = vec![
            "What are Aven's credit card benefits?",
            "How do I apply for an Aven card?",
            "What are your interest rates?",
        ];

        for case in test_cases {
            let result = engine.check_input_guardrails(case);
            assert!(!result.blocked, "Should not block: {}", case);
        }
    }
}
