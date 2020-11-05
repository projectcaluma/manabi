use base_x;
use branca;
use std::env;
const BASE62: &str = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

fn main() {
    let args: Vec<String> = env::args().collect();
    let key = base_x::decode(BASE62, &args[2]).unwrap();

    match args[1].as_ref() {
        "decode" => {
            let payload = branca::decode(&args[3], &key, 0).unwrap();
            let out = base_x::encode(BASE62, &payload.as_bytes());
            print!("{}", out);
        }
        _ => (),
    }
}
