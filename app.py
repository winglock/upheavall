from flask import Flask, render_template, jsonify
import requests
import os

app = Flask(__name__)

# 1. 메인 페이지를 보여주는 라우트
@app.route('/')
def index():
    return render_template('checker.html')

# 2. API 요청을 대신 처리해주는 프록시 라우트
@app.route('/api/check/<string:address>')
def check_eligibility(address):
    # 주소 유효성 검사
    if not (address.startswith('0x') and len(address) == 42):
        return jsonify({
            "status": "error", 
            "message": "Invalid wallet address format."
        }), 400

    target_url = f"https://app.based.one/api/pup/eligibility/{address}"
    
    # cURL 명령어의 헤더를 기반으로 실제 브라우저처럼 보이게 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'Referer': 'https://app.based.one/launchpad',
        'Accept': '*/*',
        'Accept-Language': 'ko-KR,ko;q=0.5',
        'Content-Type': 'application/json',
        'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Brave";v="140"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Gpc': '1',
        'Priority': 'u=1, i'
    }

    try:
        response = requests.get(target_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # API 응답 데이터 구조 확인 및 표준화
        if 'data' in data:
            return jsonify({
                "status": "success",
                "data": data['data']
            })
        else:
            # 만약 data 키가 없다면 전체 응답을 data로 감싸기
            return jsonify({
                "status": "success",
                "data": data
            })

    except requests.exceptions.Timeout:
        return jsonify({
            "status": "error", 
            "message": "Request timeout. Please try again."
        }), 504
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({
                "status": "error", 
                "message": "Wallet address not found or no data available."
            }), 404
        else:
            return jsonify({
                "status": "error", 
                "message": f"HTTP error: {e.response.status_code}"
            }), e.response.status_code
    
    except requests.exceptions.RequestException as e:
        print(f"Error calling external API: {e}")
        return jsonify({
            "status": "error", 
            "message": "Failed to fetch data from the external API."
        }), 502
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({
            "status": "error", 
            "message": "An unexpected error occurred."
        }), 500

# 추가: 서버 상태 확인용 엔드포인트
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "message": "Server is running"})

if __name__ == '__main__':
    # 환경변수에서 포트 설정 (배포시 유용)
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)