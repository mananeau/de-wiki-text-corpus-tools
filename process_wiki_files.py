from somajo import Tokenizer, SentenceSplitter
import os
from multiprocessing import Pool, cpu_count

PROCESS_DISCUSSION = False


def get_args_from_command_line():
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser()

    # necessary
    parser.add_argument("--data_path", type=str, help="Path to the input data. Must be in csv format.")
    parser.add_argument("--output_path", type=str, help="Path to the output folder")
    args = parser.parse_args()
    return args


def is_doc_start_line(line):
    return line.startswith('<doc')


def is_doc_end_line(line):
    return line.startswith('</doc')


def remove_discussion_suffix(sentence):
    last_location = -1

    for loc, token in enumerate(sentence):
        if token == "--" or token == "--[" or token == "---":
            last_location = loc

    if last_location > -1:
        sentence = sentence[:last_location]

    return sentence


def get_data_dirs(root_dir):
    result = []
    for _, d_, _ in os.walk(root_dir):
        for dir in d_:
            result.append(dir)
    return result


def process_text_line(line):
    tokenizer = Tokenizer()
    tokens = tokenizer.tokenize(line)

    #sentence_splitter = SentenceSplitter()
    #sentences = sentence_splitter.split(tokens)
    sentences = tokens
    result = []

    for s in sentences:

        if PROCESS_DISCUSSION:
            s = remove_discussion_suffix(s)

        if len(s) >= 4:
            sentence_string = " ".join(s)

            if PROCESS_DISCUSSION:
                # check if this line still contains a dirty comment:
                if "( CEST )" not in sentence_string and "( CET )" not in sentence_string:
                    result.append(sentence_string)
            else:
                result.append(sentence_string)

    return result


def process_directory(input_dir, output_file):
    with open(os.path.join(OUTPUT_DIR, output_file), 'a') as output_file:

        # to avoid new line at end of file
        first_line_written = False

        # r_=root, d_=directories, f_=files
        for r_, _, f_ in os.walk(input_dir):
            for file_ in f_:
                next_input_file = os.path.join(r_, file_)
                print("Reading file:", next_input_file)

                with open(next_input_file, "r") as input_file:

                    skip_next_line = False

                    for line in input_file:

                        # drop line with start tag
                        if is_doc_start_line(line):
                            skip_next_line = True
                            continue

                        # drop line with end tag
                        if is_doc_end_line(line):
                            continue

                        # skip first line to skip headline
                        if skip_next_line == True:
                            skip_next_line = False
                            continue

                        # skip empty lines
                        if len(line) <= 1:
                            continue

                        sentences = process_text_line(line)

                        for sentence in sentences:

                            # ignore blank lines and make sure that stuff like "\n" is also ignored:
                            if (PROCESS_DISCUSSION == False and len(sentence) > 2) or (
                                    PROCESS_DISCUSSION == True and len(sentence) > 72):

                                if first_line_written == True:
                                    output_file.write("\n")
                                else:
                                    first_line_written = True

                                output_file.write(sentence)


def pd(map_item):
    """Wrap call to process_directory to be called by map function"""
    input_dir, output_file = map_item
    print("Creating:", output_file)
    process_directory(input_dir, output_file)


if __name__ == '__main__':
    args = get_args_from_command_line()
    INPUT_DIR = args.data_path
    OUTPUT_DIR = args.output_path
    data_dirs = get_data_dirs(INPUT_DIR)

    call_list = []
    for dir in data_dirs:
        call_item = [os.path.join(INPUT_DIR, dir), dir + ".txt"]
        call_list.append(call_item)

    pool_size = cpu_count() * 2
    print("pool_size:", pool_size)

    with Pool(pool_size) as p:
        p.map(pd, call_list)

    print("Done!")
