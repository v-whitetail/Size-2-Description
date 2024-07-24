from .setDescription import entry as setDescription

commands = [
    setDescription
]

def start():
    for command in commands:
        command.start()

def stop():
    for command in commands:
        command.stop()