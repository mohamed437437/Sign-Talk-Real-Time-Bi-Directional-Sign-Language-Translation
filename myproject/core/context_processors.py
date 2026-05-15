def asl_sets(request):
    asl_alphabet = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
    asl_numbers = [str(i) for i in range(1, 11)]
    asl_greetings = [
        "Hello", "Thank you", "Good morning", "Good night",
        "How are you?", "I am fine", "My name is", "Nice to meet you"
    ]
    asl_days = ["Saturday","Sunday","Monday","Tuesday","Wednesday","Thursday","Friday"]
    return {
        "asl_alphabet": asl_alphabet,
        "asl_numbers": asl_numbers,
        "asl_greetings": asl_greetings,
        "asl_days": asl_days,
    }
