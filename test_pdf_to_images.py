import pymupdf
import os

def pdf_to_images_all_pages(pdf_path, output_dir, image_format="png"):
    """
    convert all pages of a pdf to individual images
    """
    # create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    # open the pdf
    doc = pymupdf.open(pdf_path)
    # get the base filename without extension
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    page_count = 0
    for page_num in range(doc.page_count):
        # get the page
        page = doc[page_num]
        # render to pixmap
        # mat = pymupdf.Matrix(8.0, 8.0) resolution control if needed
        pix = page.get_pixmap(
            # matrix=mat
            )
        # create output filename
        output_path = os.path.join(
            output_dir, 
            f"{base_name}_page_{page_num + 1}.{image_format}"
        )
        # save the image
        pix.save(output_path)
        print(f"saved: {output_path}")
        page_count += 1
    doc.close()
    print(f"converted {page_count} pages successfully!")

# usage example
pdf_to_images_all_pages("example.pdf", "output_images", "png")
