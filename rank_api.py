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

        try:
            response = requests.post(
                'https://pcmap-api.place.naver.com/graphql',
                headers=headers,
                cookies=cookies,
                data=data
            )

            # 디버깅 로그 추가
            print(f"API Request Data: {data}")
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")

            if response.status_code == 200:
                response_data = response.json()
                items = response_data[0].get('data', {}).get('restaurants', {}).get('items', [])

                for idx, item in enumerate(items, start=start):
                    if item.get('id') == company_id:
                        rank = idx
                        return rank
        except Exception as e:
            print(f"Error during API call: {e}")
            return None

    return None

@app.route('/get_rank', methods=['POST'])
def get_rank():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON format.'}), 400

        keyword = data.get('keyword')
        company_id = data.get('company_id')

        if not keyword or not company_id:
            return jsonify({
                'error': 'Missing required parameters. Please provide both keyword and company_id.'
            }), 400

        rank = get_restaurant_rank(keyword, company_id)

        if rank is None:
            return jsonify({
                'keyword': keyword,
                'company_id': company_id,
                'rank': None,
                'message': 'Restaurant not found in the search results.'
            }), 200

        return jsonify({
            'keyword': keyword,
            'company_id': company_id,
            'rank': rank,
            'message': None
        }), 200

    except Exception as e:
        print(f"Error in /get_rank: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
