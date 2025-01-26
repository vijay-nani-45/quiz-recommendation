import requests
import pandas as pd
import numpy as np
from collections import defaultdict
from sklearn.linear_model import LinearRegression
from datetime import datetime


def fetch_data(url):
    """Fetch data from a given URL and return as JSON."""
    response = requests.get(url)
    try:
        data = response.json()
        print(f"Data fetched from {url}: {data.keys() if isinstance(data, dict) else type(data)}")
        return data
    except ValueError:
        raise ValueError(f"Invalid JSON response from {url}")


def analyze_current_quiz(quiz_data, submission_data):
    """Analyze current quiz performance."""
    # Validate and extract necessary keys
    if 'questions' not in quiz_data or 'submission' not in submission_data:
        raise KeyError("The required keys 'questions' or 'submission' are missing in the data.")

    questions = pd.DataFrame(quiz_data['questions'])
    submission = pd.DataFrame(submission_data['submission'])

    analysis = questions.merge(submission, left_on='id', right_on='questionId')
    analysis['correct'] = analysis['correctOptionId'] == analysis['selectedOptionId']
    analysis['time_spent'] = pd.to_timedelta(analysis['timeSpent']).dt.total_seconds()

    return analysis


def analyze_historical_data(historical_data):
    """Analyze historical quiz performance data."""
    if 'quizzes' not in historical_data:
        raise KeyError("The required key 'quizzes' is missing in historical data.")

    historical_df = pd.DataFrame(historical_data['quizzes'])
    if 'date' not in historical_df or 'score' not in historical_df:
        raise KeyError("Historical data is missing 'date' or 'score' keys.")

    historical_df['date'] = pd.to_datetime(historical_df['date'])
    avg_score = historical_df['score'].mean()

    # Topic and difficulty performance
    topic_performance = defaultdict(lambda: {'correct': 0, 'total': 0, 'time_spent': 0})
    difficulty_performance = defaultdict(lambda: {'correct': 0, 'total': 0, 'time_spent': 0})

    for _, row in historical_df.iterrows():
        for question_id, selected_option in row['responseMap'].items():
            question = next((q for q in row['questions'] if q['id'] == question_id), None)
            if question:
                topic = question['topic']
                difficulty = question['difficulty']
                correct = question['correctOptionId'] == selected_option
                time_spent = question.get('timeSpent', 0)

                topic_performance[topic]['correct'] += int(correct)
                topic_performance[topic]['total'] += 1
                topic_performance[topic]['time_spent'] += time_spent

                difficulty_performance[difficulty]['correct'] += int(correct)
                difficulty_performance[difficulty]['total'] += 1
                difficulty_performance[difficulty]['time_spent'] += time_spent

    topic_accuracy = {topic: data['correct'] / data['total'] for topic, data in topic_performance.items()}
    difficulty_accuracy = {diff: data['correct'] / data['total'] for diff, data in difficulty_performance.items()}

    return avg_score, topic_accuracy, difficulty_accuracy, historical_df


def generate_insights(current_analysis, avg_score, topic_accuracy, difficulty_accuracy, historical_df):
    """Generate insights from current and historical analysis."""
    current_score = current_analysis['correct'].mean() * 100
    weak_areas = current_analysis[~current_analysis['correct']]['topic'].value_counts().index.tolist()

    # Time-based analysis
    historical_df['days_ago'] = (datetime.now() - historical_df['date']).dt.days
    X = historical_df[['days_ago']]
    y = historical_df['score']
    model = LinearRegression().fit(X, y)
    trend = "improving" if model.coef_[0] > 0 else "declining"

    # Difficulty-based analysis
    current_difficulty_performance = current_analysis.groupby('difficulty')['correct'].mean()

    insights = {
        'current_score': current_score,
        'average_score': avg_score * 100,
        'weak_areas': weak_areas,
        'topic_accuracy': topic_accuracy,
        'difficulty_accuracy': difficulty_accuracy,
        'current_difficulty_performance': current_difficulty_performance,
        'performance_trend': trend
    }

    return insights


def create_recommendations(insights):
    """Generate recommendations based on insights."""
    recommendations = []

    if insights['current_score'] < insights['average_score']:
        recommendations.append("Your current score is below your average. Focus on improving your overall performance.")

    for topic in insights['weak_areas'][:3]:
        recommendations.append(f"Review the topic '{topic}' as it appears to be a weak area in your current quiz.")

    low_accuracy_topics = sorted(insights['topic_accuracy'].items(), key=lambda x: x[1])[:3]
    for topic, accuracy in low_accuracy_topics:
        recommendations.append(f"Work on improving your understanding of '{topic}'. Your historical accuracy is {accuracy:.2%}.")

    # Difficulty-based recommendations
    difficulty_levels = ['easy', 'medium', 'hard']
    current_performance = insights['current_difficulty_performance']
    historical_performance = insights['difficulty_accuracy']

    for difficulty in difficulty_levels:
        if difficulty in current_performance and difficulty in historical_performance:
            if current_performance[difficulty] < historical_performance[difficulty]:
                recommendations.append(f"Your performance on {difficulty} questions has dropped. Consider focusing more on {difficulty} level questions.")

    # Time-based recommendation
    recommendations.append(f"Your overall performance trend is {insights['performance_trend']}. "
                           f"{'Keep up the good work!' if insights['performance_trend'] == 'improving' else 'Try to identify areas for improvement.'}")

    return recommendations


def main():
    """Main function to execute the script."""
    print("Fetching data...")
    quiz_data = fetch_data('https://jsonkeeper.com/b/LLQT')
    submission_data = fetch_data('https://api.jsonserve.com/rJvd7g')
    historical_data = fetch_data('https://api.jsonserve.com/XgAgFJ')

    print("Analyzing current quiz...")
    current_analysis = analyze_current_quiz(quiz_data, submission_data)

    print("Analyzing historical data...")
    avg_score, topic_accuracy, difficulty_accuracy, historical_df = analyze_historical_data(historical_data)

    print("Generating insights...")
    insights = generate_insights(current_analysis, avg_score, topic_accuracy, difficulty_accuracy, historical_df)

    print("Creating recommendations...")
    recommendations = create_recommendations(insights)

    # Print results
    print("\n--- Insights ---")
    print(f"Current Score: {insights['current_score']:.2f}%")
    print(f"Average Score: {insights['average_score']:.2f}%")
    print(f"Weak Areas: {', '.join(insights['weak_areas'][:3])}")
    print(f"Performance Trend: {insights['performance_trend']}")

    print("\n--- Topic Accuracy ---")
    for topic, accuracy in insights['topic_accuracy'].items():
        print(f"{topic}: {accuracy:.2%}")

    print("\n--- Difficulty Accuracy ---")
    for difficulty, accuracy in insights['difficulty_accuracy'].items():
        print(f"{difficulty}: {accuracy:.2%}")

    print("\n--- Current Difficulty Performance ---")
    for difficulty, performance in insights['current_difficulty_performance'].items():
        print(f"{difficulty}: {performance:.2%}")

    print("\n--- Recommendations ---")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")


if __name__ == "__main__":
    main()
