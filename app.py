


import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# Fetch data from APIs with error handling
def fetch_data(url):
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()  # Raise an exception for bad responses
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        st.error(f"Other error occurred: {err}")
    return {}

# Process current quiz data with error handling
def process_current_quiz(data):
    try:
        questions = data.get('questions', [])
        if not questions:
            st.warning("No questions available in the current quiz data.")
            return pd.DataFrame()  # Return an empty DataFrame if no data found
        df = pd.DataFrame(questions)
        df['correct'] = df['correct_answer'] == df['selected_option']
        return df
    except KeyError as e:
        st.error(f"Key error: {e}")
    except Exception as e:
        st.error(f"Error processing current quiz data: {e}")
    return pd.DataFrame()

# Process historical quiz data with error handling
def process_historical_quizzes(data):
    try:
        if 'quizzes' not in data:
            st.warning("No quizzes available in the historical data.")
            return pd.DataFrame()  # Return an empty DataFrame if no data found
        historical_data = []
        for quiz in data['quizzes']:
            quiz_data = {
                'quiz_id': quiz['quiz_id'],
                'score': quiz['score'],
                'total_questions': quiz['total_questions'],
                'correct_answers': sum(1 for v in quiz['response_map'].values() if v == 1)
            }
            historical_data.append(quiz_data)
        return pd.DataFrame(historical_data)
    except KeyError as e:
        st.error(f"Key error: {e}")
    except Exception as e:
        st.error(f"Error processing historical quizzes: {e}")
    return pd.DataFrame()

# Generate insights based on the data
def generate_insights(current_quiz, historical_quizzes):
    insights = []
    if not current_quiz.empty:
        weak_topics = current_quiz[~current_quiz['correct']]['topic'].value_counts().index.tolist()
        insights.append(f"Weak areas in the current quiz: {', '.join(weak_topics[:3])}")

        accuracy = current_quiz['correct'].mean() * 100
        insights.append(f"Current quiz accuracy: {accuracy:.2f}%")
    
    if not historical_quizzes.empty:
        avg_score = historical_quizzes['score'].mean()
        insights.append(f"Average score in last 5 quizzes: {avg_score:.2f}")

        score_trend = historical_quizzes['score'].diff().mean()
        trend_direction = "improving" if score_trend > 0 else "declining"
        insights.append(f"Your performance is {trend_direction} over the last 5 quizzes")

    return insights

# Generate recommendations based on the data
def generate_recommendations(current_quiz, historical_quizzes):
    recommendations = []
    if not current_quiz.empty:
        weak_topics = current_quiz[~current_quiz['correct']]['topic'].value_counts().index.tolist()
        recommendations.append(f"Focus on these topics: {', '.join(weak_topics[:3])}")

        avg_difficulty = current_quiz['difficulty'].mean()
        if avg_difficulty < 2:
            recommendations.append("Try attempting more difficult questions to challenge yourself")
        elif avg_difficulty > 4:
            recommendations.append("Consider practicing easier questions to build confidence")

        if current_quiz['time_taken'].mean() > 90:  # Assuming 90 seconds is the threshold
            recommendations.append("Work on improving your time management skills")
    
    return recommendations

# Streamlit app main function
def main():
    st.title("Personalized Student Recommendations")
    
    # Fetch and process data
    current_quiz_data = fetch_data("https://jsonkeeper.com/b/LLQT")
    current_quiz_submission = fetch_data("https://api.jsonserve.com/rJvd7g")
    historical_data = fetch_data("https://api.jsonserve.com/XgAgFJ")
    
    current_quiz = process_current_quiz(current_quiz_data)
    historical_quizzes = process_historical_quizzes(historical_data)
    
    # Generate insights and recommendations
    insights = generate_insights(current_quiz, historical_quizzes)
    recommendations = generate_recommendations(current_quiz, historical_quizzes)
    
    # Display insights
    st.header("Insights")
    for insight in insights:
        st.write(f"• {insight}")
    
    # Display recommendations
    st.header("Recommendations")
    for recommendation in recommendations:
        st.write(f"• {recommendation}")
    
    # Visualize performance trend
    if not historical_quizzes.empty:
        st.header("Performance Trend")
        fig, ax = plt.subplots()
        ax.plot(historical_quizzes['quiz_id'], historical_quizzes['score'], marker='o')
        ax.set_xlabel("Quiz ID")
        ax.set_ylabel("Score")
        ax.set_title("Performance Trend in Last 5 Quizzes")
        st.pyplot(fig)

if __name__ == "__main__":
    main()
