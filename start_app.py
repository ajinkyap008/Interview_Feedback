from flask import Flask, render_template, request
from SpeechBrain import do_script
import requests as requests
import json as json


def get_gpt_feedback(interview_speech_prompt):
    end_point = 'https://api.openai.com/v1/completions'
    request_body = {"model": "text-davinci-003", "prompt": interview_speech_prompt, "temperature": 0, "max_tokens": 2500}
    request_headers = {'Authorization': 'Bearer ', 'Content-Type': 'application/json'} #OpenAPI token required
    print('POST CALL')
    gpt_response = requests.post(end_point, data=json.dumps(request_body), headers=request_headers)
    print('POST CALL DONE')
    parsed_response = json.loads(gpt_response.content)["choices"]
    for response_field in parsed_response:
        interview_feedback = response_field['text']
    return interview_feedback

app = Flask(__name__)

candidate_email = ""
candidate_name = ""
candidate_id = ""

@app.route('/start')
def hello_world():
    return render_template('index.html')

@app.route('/review-data', methods = ['POST'])
def hello_world2():
    if request.method == 'POST':
        form_dict = request.form.to_dict()
        print(form_dict)
        candidate_email = form_dict.get("exampleInputEmail1")
        candidate_id = form_dict.get("exampleInputId1")
        candidate_name = form_dict.get("exampleInputName1")

        do_script("./video_file/interviewFile.mp4")#add path to interview file video
        text_file = open("InterviewTranscript.txt", "r")
        raw_interview_data = text_file.read()
        basic_insights_data = get_gpt_feedback("Analyse below interview transcript: \n" + raw_interview_data)
        evaluation_data = get_gpt_feedback("Evaluate candidate from interview transcript: \n" + raw_interview_data)
        qualitative_data = get_gpt_feedback("Analyse the transcript for Quantitative analysis for developer position based on technical skills in percentage against following transcript and return response as json: \n" + raw_interview_data)
        top_three_data = get_gpt_feedback("Extract top three qualities of candidate from following interview transcript: \n" + raw_interview_data)
        interviewer_feedback = get_gpt_feedback("Based on the questions asked, create the feedback for interviewer from below transcript: \n" + raw_interview_data)
        text_file.close()
        print(basic_insights_data, evaluation_data, qualitative_data, top_three_data)
        print(basic_insights_data, evaluation_data, clean_qual_data(qualitative_data), clean_data(top_three_data.split("\n")))
        return render_template('feedback.html', candidate_email=candidate_email, candidate_id=candidate_id, candidate_name=candidate_name, basic_data=basic_insights_data, eval_data=evaluation_data, qual_data=clean_qual_data(qualitative_data), top_three_data=clean_data(top_three_data.split("\n")), interviewer_feedback=interviewer_feedback)
    else:
        return "<h3>Method not Supported</h3>"

def clean_qual_data(qualitative_data):
    json_expr = "{"+qualitative_data.partition("{")[2]
    the_dict = json.loads(json_expr)
    if 'Technical Skills' in the_dict.keys():
        tech_skill_dict = the_dict['Technical Skills']
    else:
        tech_skill_dict = the_dict
    cleaned_qual_data = []
    for key in tech_skill_dict:
        cleaned_qual_data.append([key, str(tech_skill_dict[key])])

    print(cleaned_qual_data)
    return cleaned_qual_data

def clean_data(list_data):
    return_list = []
    for x in list_data:
        if x not in [None,'',', ',',']:
            return_list.append(x)
    
    return return_list

if __name__ == '__main__':
    print("running..")
    app.run(host='0.0.0.0', port=8080)
    print("end")
