import os
import requests
import urllib3
import SpecialFriend_pb2
import time
from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

urllib3.disable_warnings()
app = Flask(__name__)

# --- Configuration ---
GUEST_UID = "4338419284"
GUEST_PASSWORD = "CKR_IMQQB__LCG9J"
AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'
BASE_URL = "https://clientbp.ggpolarbear.com"

def dec(d):
    try:
        return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(d), 16)
    except:
        return d

def build_uid_protobuf(uid):
    def to_varint(n):
        res = bytearray()
        while n >= 0x80:
            res.append((n & 0x7f) | 0x80)
            n >>= 7
        res.append(n)
        return bytes(res)
    
    # Encrypting UID with Protobuf tag \x08
    raw_data = b"\x08" + to_varint(int(uid))
    return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(raw_data, 16))

def format_timestamp(ts):
    try:
        return time.strftime('%B %d, %Y at %I:%M %p', time.localtime(ts))
    except:
        return "Unknown Date"

def fetch_jwt_token():
    # Naya API URL format
    url = f"https://ff-jwt-gen-api.lovable.app/api/public/token?uid={GUEST_UID}&password={GUEST_PASSWORD}"
    try:
        r = requests.get(url, timeout=10)
        # Yedi API le JSON ma token dincha bhane .json().get("token") garnu, 
        # natra r.text use garnu.
        return r.json().get("token") if r.status_code == 200 else None
    except:
        return None

@app.route('/')
def home():
    return jsonify({"status": "Online", "developer": "CKRPRO"})

@app.route('/api/duo', methods=['GET'])
def get_duo():
    uid = request.args.get('uid')
    if not uid or not uid.isdigit():
        return jsonify({"error": "Invalid UID"}), 400

    jwt = fetch_jwt_token()
    if not jwt:
        return jsonify({"error": "Token generation failed"}), 500

    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB53"
    }

    try:
        payload = build_uid_protobuf(uid)
        resp = requests.post(f"{BASE_URL}/GetSpecialFriendList", headers=headers, data=payload, timeout=15, verify=False)
        
        if resp.status_code == 200:
            decrypted = dec(resp.content)
            response_pb = SpecialFriend_pb2.SpecialFriendResponse()
            response_pb.ParseFromString(decrypted)

            if not response_pb.HasField("duo_info"):
                return jsonify({"success": False, "message": "No Duo Found", "developer": "CKRPRO"}), 404

            duo = response_pb.duo_info
            score = duo.score
            
            # Level Logic
            if score < 101: lvl = 1
            elif score < 301: lvl = 2
            elif score < 501: lvl = 3
            elif score < 801: lvl = 4
            elif score < 1201: lvl = 5
            else: lvl = 6

            return jsonify({
                "success": True,
                "data": {
                    "partner_uid": str(duo.partner_uid),
                    "intimacy_score": score,
                    "duo_level": f"Level {lvl}",
                    "days_active": f"{duo.days_active} Days",
                    "created_on": format_timestamp(duo.creation_timestamp),
                    "status": "Active" if getattr(duo, "status", 0) == 2 else "Inactive"
                },
                "developer": "CKRPRO",
                "youtube": "CKR UNKNOWN",
                "tiktok": "ckrunknown"
            })
        
        return jsonify({"error": f"Server Status {resp.status_code}"}), resp.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
