use rdev::{listen, Event, EventType};
use serde::Serialize;
use serde_json::json;

#[derive(Serialize)]
struct RdevEvent {
    event_type: String,
    name: Option<String>,
    time: std::time::SystemTime,
    data: String,
}

fn deal_event_to_json(event: Event) -> RdevEvent {
    let mut jsonify_event = RdevEvent {
        event_type: "".to_string(),
        name: event.name,
        time: event.time,
        data: "".to_string(),
    };
    match event.event_type {
        EventType::KeyPress(key) => {
            jsonify_event.event_type = "KeyPress".to_string();
            jsonify_event.data = json!({
                "key": format!("{:?}", key)
            })
            .to_string();
        }
        EventType::KeyRelease(key) => {
            jsonify_event.event_type = "KeyRelease".to_string();
            jsonify_event.data = json!({
                "key": format!("{:?}", key)
            })
            .to_string();
        }
        EventType::MouseMove { x, y } => {
            jsonify_event.event_type = "MouseMove".to_string();
            jsonify_event.data = json!({
                "x": x,
                "y": y
            })
            .to_string();
        }
        EventType::ButtonPress(key) => {
            jsonify_event.event_type = "ButtonPress".to_string();
            jsonify_event.data = json!({
                "key": format!("{:?}", key)
            })
            .to_string();
        }
        EventType::ButtonRelease(key) => {
            jsonify_event.event_type = "ButtonRelease".to_string();
            jsonify_event.data = json!({
                "key": format!("{:?}", key)
            })
            .to_string();
        }
        EventType::Wheel { delta_x, delta_y } => {
            jsonify_event.event_type = "Wheel".to_string();
            jsonify_event.data = json!({
                "delta_x": delta_x,
                "delta_y": delta_y
            })
            .to_string();
        }
    }

    jsonify_event
}

// OLD: Slow character-by-character method (kept as fallback)
fn write_text_slow(text: &str) {
    use enigo::{Enigo, Keyboard, Settings};
    let mut enigo = Enigo::new(&Settings::default()).unwrap();
    enigo.text(text).unwrap();
}

// NEW: Fast clipboard + Ctrl+V method
fn write_text_fast(text: &str) {
    use clipboard_win::{formats, set_clipboard, get_clipboard_string};
    use enigo::{Enigo, Key, Keyboard, Settings, Direction};
    
    // Save current clipboard content
    let old_clipboard = get_clipboard_string().unwrap_or_default();
    
    // Set new text to clipboard
    if let Err(e) = set_clipboard(formats::Unicode, text) {
        eprintln!("Failed to set clipboard: {:?}", e);
        // Fallback to slow method if clipboard fails
        write_text_slow(text);
        return;
    }
    
    // Small delay to ensure clipboard is ready
    std::thread::sleep(std::time::Duration::from_millis(30));
    
    // Simulate Ctrl+V (paste)
    let mut enigo = Enigo::new(&Settings::default()).unwrap();
    
    // Press Ctrl
    if let Err(e) = enigo.key(Key::Control, Direction::Press) {
        eprintln!("Failed to press Ctrl: {:?}", e);
        write_text_slow(text);
        return;
    }
    
    // Press V
    if let Err(e) = enigo.key(Key::Unicode('v'), Direction::Click) {
        eprintln!("Failed to press V: {:?}", e);
    }
    
    // Release Ctrl
    if let Err(e) = enigo.key(Key::Control, Direction::Release) {
        eprintln!("Failed to release Ctrl: {:?}", e);
    }
    
    // Wait for paste to complete
    std::thread::sleep(std::time::Duration::from_millis(100));
    
    // Restore original clipboard content
    if !old_clipboard.is_empty() {
        let _ = set_clipboard(formats::Unicode, &old_clipboard);
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();

    if args.len() > 1 && args[1] == "listen" {
        if let Err(error) = listen(move |event| match event.event_type {
            EventType::KeyPress(_) | EventType::KeyRelease(_) => {
                let event = deal_event_to_json(event);
                println!("{}", serde_json::to_string(&event).unwrap());
            }

            _ => {}
        }) {
            println!("!error: {:?}", error);
        }
    }

    // Fast write using clipboard + Ctrl+V
    if args.len() > 2 && args[1] == "write" {
        let text = args[2].clone();
        write_text_fast(text.as_str());
    }
    
    // Fallback: slow write using character simulation (for compatibility)
    if args.len() > 2 && args[1] == "write-slow" {
        let text = args[2].clone();
        write_text_slow(text.as_str());
    }
    
    // Toggle CapsLock state (used to revert after recording)
    if args.len() > 1 && args[1] == "toggle-caps" {
        use enigo::{Enigo, Key, Keyboard, Settings, Direction};
        let mut enigo = Enigo::new(&Settings::default()).unwrap();
        // Press and release CapsLock to toggle its state
        let _ = enigo.key(Key::CapsLock, Direction::Click);
    }
}
