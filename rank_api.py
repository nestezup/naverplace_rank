from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

def get_restaurant_rank(keyword, company_id):
    headers = {
        'accept': '*/*',
        'accept-language': 'ko',
        'content-type': 'application/json',
        'origin': 'https://pcmap.place.naver.com',
        'referer': 'https://pcmap.place.naver.com/place/list',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    }

    cookies = {
        'NNB': 'ULAV2ESVGWUGM',
    }

    query = """
    query getRestaurants($restaurantListInput: RestaurantListInput) {
      restaurants: restaurantList(input: $restaurantListInput) {
        items {
          id
          name
        }
      }
    }
    """

    # 순위를 찾기 위한 변수
    rank = None
    
    # 1부터 300까지 50개씩 검색
    for start in range(1, 301, 50):
        variables = {
            "restaurantListInput": {
                "query": keyword,
                "start": start,
                "display": 50,
                "deviceType": "pcmap",
                "isPcmap": True
            }
        }
        
        data = json.dumps([{
            "operationName": "getRestaurants",
            "variables": variables,
            "query": query
        }])

        response = requests.post('https://pcmap-api.place.naver.com/graphql', 
                               headers=headers, 
                               cookies=cookies, 
                               data=data)

        if response.status_code == 200:
            try:
                response_data = response.json()
                items = response_data[0]['data']['restaurants']['items']
                
                # 현재 페이지에서 업체 검색
                for idx, item in enumerate(items, start=start):
                    if item['id'] == company_id:
                        rank = idx
                        return rank  # 순위를 찾으면 즉시 반환
                
            except (json.JSONDecodeError, KeyError) as e:
                return None
        else:
            return None
    
    return None  # 업체를 찾지 못한 경우

@app.route('/get_rank', methods=['POST'])
def get_rank():
    try:
        data = request.get_json()
        keyword = data.get('keyword')
        company_id = data.get('company_id')
        
        if not keyword or not company_id:
            return jsonify({
                'error': 'Missing required parameters. Please provide both keyword and company_id.'
            }), 400
            
        rank = get_restaurant_rank(keyword, company_id)
        
        if rank is not None:
            return jsonify({
                'keyword': keyword,
                'company_id': company_id,
                'rank': rank
            })
        else:
            return jsonify({
                'error': 'Restaurant not found or error occurred during search'
            }), 404
            
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
