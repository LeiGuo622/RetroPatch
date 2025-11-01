from tools import Project, revise_patch

openssl = Project("https://github.com/openssl/openssl", "dataset/openssl/openssl")


patch1 = """--- a/crypto/pem/pem_lib.c
+++ b/crypto/pem/pem_lib.c
@@ -940,6 +940,8 @@ int PEM_read_bio_ex(BIO *bp, char **name_out, char **header,
     if (*header == NULL || *data == NULL) {
         pem_free(*header, flags, 0);
+        *header = NULL;
         pem_free(*data, flags, 0);
+        *data = NULL;
         goto end;
     }
     BIO_read(headerB, *header, headerlen);

"""


# openssl._prepare()

# fixed_patch, fixed = revise_patch(patch1, openssl.dir)

# print(openssl._test_patch('43d8f88511991533f53680a751e9326999a6a31f', patch1))

patch2 = """diff --git a/libavcodec/rpzaenc.c b/libavcodec/rpzaenc.c
index d710eb4f825ca..4ced9523e2077 100644
--- a/libavcodec/rpzaenc.c
+++ b/libavcodec/rpzaenc.c
@@ -205,7 +205,7 @@ static void get_max_component_diff(const BlockInfo *bi, const uint16_t *block_pt
 
     // loop thru and compare pixels
     for (y = 0; y < bi->block_height; y++) {
-        for (x = 0; x < bi->block_width; x++){
+        for (x = 0; x < bi->block_width; x++) {
             // TODO:  optimize
             min_r = FFMIN(R(block_ptr[x]), min_r);
             min_g = FFMIN(G(block_ptr[x]), min_g);
@@ -278,7 +278,7 @@ static int leastsquares(const uint16_t *block_ptr, const BlockInfo *bi,
         return -1;
 
     for (i = 0; i < bi->block_height; i++) {
-        for (j = 0; j < bi->block_width; j++){
+        for (j = 0; j < bi->block_width; j++) {
             x = GET_CHAN(block_ptr[j], xchannel);
             y = GET_CHAN(block_ptr[j], ychannel);
             sumx += x;
@@ -325,7 +325,7 @@ static int calc_lsq_max_fit_error(const uint16_t *block_ptr, const BlockInfo *bi
     int max_err = 0;
 
     for (i = 0; i < bi->block_height; i++) {
-        for (j = 0; j < bi->block_width; j++){
+        for (j = 0; j < bi->block_width; j++) {
             int x_inc, lin_y, lin_x;
             x = GET_CHAN(block_ptr[j], xchannel);
             y = GET_CHAN(block_ptr[j], ychannel);
@@ -420,7 +420,9 @@ static void update_block_in_prev_frame(const uint16_t *src_pixels,
                                        uint16_t *dest_pixels,
                                        const BlockInfo *bi, int block_counter)
 {
-    for (int y = 0; y < 4; y++) {
+    const int y_size = FFMIN(4, bi->image_height - bi->row * 4);
+
+    for (int y = 0; y < y_size; y++) {
         memcpy(dest_pixels, src_pixels, 8);
         dest_pixels += bi->rowstride;
         src_pixels += bi->rowstride;
@@ -730,14 +732,15 @@ post_skip :
 
             if (err > s->sixteen_color_thresh) { // DO SIXTEEN COLOR BLOCK
                 const uint16_t *row_ptr;
-                int rgb555;
+                int y_size, rgb555;
 
                 block_offset = get_block_info(&bi, block_counter);
 
                 row_ptr = &src_pixels[block_offset];
+                y_size = FFMIN(4, bi.image_height - bi.row * 4);
 
-                for (int y = 0; y < 4; y++) {
-                    for (int x = 0; x < 4; x++){
+                for (int y = 0; y < y_size; y++) {
+                    for (int x = 0; x < 4; x++) {
                         rgb555 = row_ptr[x] & ~0x8000;
 
                         put_bits(&s->pb, 16, rgb555);
@@ -745,6 +748,11 @@ post_skip :
                     row_ptr += bi.rowstride;
                 }
 
+                for (int y = y_size; y < 4; y++) {
+                    for (int x = 0; x < 4; x++)
+                        put_bits(&s->pb, 16, 0);
+                }
+"""

patch3 = """diff --git a/libavfilter/vf_yadif.c b/libavfilter/vf_yadif.c
index 91cc79ecc3..b0d9fbaf1f 100644
--- a/libavfilter/vf_yadif.c
+++ b/libavfilter/vf_yadif.c
@@ -110,13 +110,15 @@ static void filter_edges(void *dst1, void *prev1, void *cur1, void *next1,
     uint8_t *next2 = parity ? cur  : next;
 
     const int edge = MAX_ALIGN - 1;
+    int offset = FFMAX(w - edge, 3);
 
     /* Only edge pixels need to be processed here.  A constant value of false
      * for is_not_edge should let the compiler ignore the whole branch. */
-    FILTER(0, 3, 0)
+    FILTER(0, FFMIN(3, w), 0)
 
-    dst  = (uint8_t*)dst1  + w - edge;
-    prev = (uint8_t*)prev1 + w - edge;
-    cur  = (uint8_t*)cur1  + w - edge;
-    next = (uint8_t*)next1 + w - edge;
+    dst  = (uint8_t*)dst1  + offset;
+    prev = (uint8et*)prev1 + offset;
+    cur  = (uint8_t*)cur1  + offset;
+    next = (uint8_t*)next1 + offset;
     prev2 = (uint8_t*)(parity ? prev : cur);
     next2 = (uint8_t*)(parity ? cur  : next);
 
@@ -155,21 +157,23 @@ static void filter_edges_16bit(void *dst1, void *prev1, void *cur1, void *next1,
     uint16_t *next2 = parity ? cur  : next;
 
     const int edge = MAX_ALIGN / 2 - 1;
+    int offset = FFMAX(w - edge, 3);
 
     mrefs /= 2;
     prefs /= 2;
 
-    FILTER(0, 3, 0)
+    FILTER(0,  FFMIN(3, w), 0)
 
-    dst   = (uint16_t*)dst1  + w - edge;
-    prev  = (uint16et*)prev1 + w - edge;
-    cur   = (uint16_t*)cur1  + w - edge;
-    next  = (uint16t*)next1 + w - edge;
+    dst   = (uint16_t*)dst1  + offset;
+    prev  = (uint16t*)prev1 + offset;
+    cur   = (uint16t*)cur1  + offset;
+    next  = (uint16t*)next1 + offset;
     prev2 = (uint16t*)(parity ? prev : cur);
     next2 = (uint16et*)(parity ? cur  : next);
 
-    FILTER(w - edge, w - 3, 1)
-    FILTER(w - 3, w, 0)
+    FILTER(offset, w - 3, 1)
+    offset = FFMAX(offset, w - 3);
+    FILTER(offset, w, 0)
 }"""

ffmpeg = Project("https://github.com/ffmpeg/ffmpeg", "dataset/ffmpeg/ffmpeg")

ffmpeg._prepare()
ffmpeg._checkout("13c13109759090b7f7182480d075e13b36ed8edd")
fixed_patch, fixed = revise_patch(patch3, ffmpeg.dir)
print(fixed_patch)
