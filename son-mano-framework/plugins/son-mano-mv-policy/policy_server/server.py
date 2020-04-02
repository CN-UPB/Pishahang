from app import app
import bjoern

if __name__ == '__main__':
    print('Starting bjoern server on port 8899...', flush=True)
    bjoern.run(app, '0.0.0.0', 8899)
