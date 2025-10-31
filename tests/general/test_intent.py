from src.retrieval.intent_classifier import IntentClassifier, QueryIntent

# Test just the intent classification
classifier = IntentClassifier()
factual_query = 'When was AI founded?'
exploratory_query = 'Tell me about renewable energy'

factual_intent = classifier.classify(factual_query)
exploratory_intent = classifier.classify(exploratory_query)

print(f'Factual query: "{factual_query}" -> {factual_intent.primary_intent.value}')
print(f'Exploratory query: "{exploratory_query}" -> {exploratory_intent.primary_intent.value}')
