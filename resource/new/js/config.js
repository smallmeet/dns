var config = {
    "test": {
        "sub_domain_result_ws": "ws://192.168.1.124:8888/result_ws_test",
        "reverse_ip_result_ws": "ws://192.168.1.124:8888/result_ws_test",
        "domain": {"domain": "kq88.com"}
    },
    "real": {
        "sub_domain_result_ws": "ws://" + location.host + "/result_ws_test",
        "reverse_ip_result_ws": "ws://" + location.host + "/reverse_ip_result_ws"
    }
};
var env = "test";
var env_config = config[env];