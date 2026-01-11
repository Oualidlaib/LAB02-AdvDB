import os

record_data = b'\x42\x42\x42\x42\x42\x42'

PAGE_SIZE = 4096  # Each page is 4 KB


def create_heap_file(file_name):
    with open(file_name, 'wb') as f:  # Open in write-binary mode
        pass


def read_page(file_name, page_number):
    """Read a specific page (4 KB) from the heap file given the page number."""    
    # Check if the file has enough pages to contain the requested page
    file_size = os.path.getsize(file_name)
    last_page_number  = file_size // PAGE_SIZE - 1
    
    if page_number > last_page_number:
        raise ValueError(f"Page {page_number} does not exist in the file.")

    with open(file_name, 'rb') as f:
        f.seek(page_number * PAGE_SIZE)  # Go to the start of the specified page
        page_data = f.read(PAGE_SIZE)  # Read the 4 KB page
    return page_data



def append_page(file_name, page_data):
    """Appends the provided page data to the end of the file."""
    if len(page_data) != PAGE_SIZE:
        raise ValueError(f"Page data must be exactly {PAGE_SIZE} bytes.")
    
    with open(file_name, 'ab') as f:  # Open in append-binary mode
        f.write(page_data)  # Append the page data to the end of the file


def write_page(file_name, page_number, page_data):
    """Write data to a specific page in the heap file."""
    # Check if the file has enough pages to contain the requested page
    file_size = os.path.getsize(file_name)
    last_page_number  = file_size // PAGE_SIZE -1
    
    if page_number > last_page_number:
        raise ValueError(f"Page {page_number} does not exist in the file.")
    if len(page_data) != PAGE_SIZE:
        raise ValueError(f"Data must be exactly {PAGE_SIZE} bytes long.")
    
    with open(file_name, 'r+b') as f:  # Open for reading and writing in binary mode
        f.seek(page_number * PAGE_SIZE)  # Go to the start of the specified page
        f.write(page_data)  # Write the data to the page

################################################################################################################

def Calculate_free_space(page_data):
    
    # subtract directly the size of the first slot directory entry (pointer of the free space and slot count)
    free_space = PAGE_SIZE - 4

    # get slot count
    slot_count = int.from_bytes(page_data[PAGE_SIZE-4:PAGE_SIZE-2], 'big')

    # substract from the free space the size of the records entries in the slot directory
    free_space = free_space - 4 * slot_count

    # subtract from the free space how much each record occupy
    start = PAGE_SIZE - 8 # 4088
    end = PAGE_SIZE - 4 # 4092
    for i in range(slot_count):

        # get record length from the entry
        record_length = int.from_bytes(page_data[start:end-2], 'big')

        # subtract record length from free_space
        free_space = free_space - record_length

        # update start and end to the new byte indices
        start = start - 4
        end = end - 4
    
    # return the final result 
    return free_space

################################################################################################################

def insert_record_data_to_page_data(page_data, record_data):

    # get record_length
    record_length = len(record_data)

    # check the free space vs record length (This is a redundant check since the function is \
    #                                       only called if there is enough free space)
    if Calculate_free_space(page_data) < record_length + 4:
        raise ValueError("There is no free space to insert the record in the page")
    
    # get the free space offset
    free_space_offset = int.from_bytes(page_data[PAGE_SIZE-2:], 'big')

    # read the slot count
    slot_count = int.from_bytes(page_data[PAGE_SIZE-4:PAGE_SIZE-2], 'big')

    # insert record_data starting from free space offset
    page_data = page_data[:free_space_offset] + record_data + page_data[free_space_offset + record_length:]

    # insert a new slot entry (offset and length) of the inserted record
    record_offset = free_space_offset
    free_space_offset = free_space_offset + record_length
    slot_count = slot_count + 1

    slot_entry_start = PAGE_SIZE - 4 * slot_count - 4
    record_offset_bytes = record_offset.to_bytes(2, 'big')
    record_length_bytes = record_length.to_bytes(2, 'big')

    page_data = page_data[:slot_entry_start] + \
                record_length_bytes + record_offset_bytes + \
                page_data[slot_entry_start+4:]
    
    # update slot count and free space offset
    free_space_offset_bytes = free_space_offset.to_bytes(2, 'big')
    slot_count_bytes = slot_count.to_bytes(2, 'big')

    page_data = page_data[:PAGE_SIZE-4] + slot_count_bytes + free_space_offset_bytes

    # returns the page_data with inserted record in bytes format
    return page_data

################################################################################################################

def insert_record_to_file(file_name, record_data):

    page_data = []

    # Assuming there is no page with enough free space exist
    page_number = -1

    # get the length of the record
    record_length = len(record_data)

    # get the number of pages in the file
    file_size = os.path.getsize(file_name)
    num_pages  = file_size // PAGE_SIZE 

    for i in range(num_pages):
        page_data = read_page(file_name, i)

        # test if there is enough free space
        if Calculate_free_space(page_data) >= record_length + 4:

            # update if a page is found
            page_number = i

            # get out from the loop
            break

    # If there is no free free space or the file is empty, create new data page of 4096 bytes
    if(page_number == -1):
        page_data = bytearray(PAGE_SIZE)

    # call insert_record_data_to_page_data function
    page_data = insert_record_data_to_page_data(page_data, record_data)
    
    # write or append the page
    if(page_number == -1):
        append_page(file_name, page_data)
    else:
        write_page(file_name, page_number, page_data)

################################################################################################################

def get_record_from_page(page_data, record_id):

    # Check whether there is such a record with that Id by comparing it with slot count
    slot_count = int.from_bytes(page_data[PAGE_SIZE-4:PAGE_SIZE-2], 'big')

    if(slot_count < record_id):
        raise ValueError(f"There no such a record with id {record_id}")
    else:
        # get the corresponding slot entry
        slot_entry_start = (PAGE_SIZE - 4) - 4 * record_id

        # get record length and offset
        record_length = int.from_bytes(page_data[ slot_entry_start : slot_entry_start + 2 ], 'big')
        record_offset = int.from_bytes(page_data[ slot_entry_start + 2 : slot_entry_start + 4 ], 'big')

        # retrive the record from the page
        record_data = page_data[ record_offset : record_offset + record_length ]

        # return the record
        return record_data

################################################################################################################

def get_record_from_file(file_name, page_number, record_id):
    
    # retrieve the page from the file
    page_data = read_page(file_name, page_number)

    # get the record from the page
    record_data = get_record_from_page(page_data, record_id)

    # return the result
    return record_data

################################################################################################################

def get_all_record_from_page(page_data):

    # get slot count of the page
    slot_count = int.from_bytes(page_data[PAGE_SIZE-4:PAGE_SIZE-2], 'big')

    # define a list to store the records of the page
    records = []

    for record_id in range(1, slot_count + 1):

        # get the record from the page and append it to the records list
        records.append( get_record_from_page(page_data, record_id) )
    
    # return the list of records
    return records

################################################################################################################

def get_all_records_from_file(file_name):
  
    # get the number of pages of that file
    file_size = os.path.getsize(file_name)
    num_pages  = file_size // PAGE_SIZE 

    # define a list to store the records
    records = []

    # Loop through each page and append the result to the records list
    for page_num in range(num_pages):

        # retrieve the page from the file
        page_data = read_page(file_name, page_num)

        # extend the records list
        records.extend(
                        get_all_record_from_page(page_data)
                      )
    
    # return the set of records 
    return records



