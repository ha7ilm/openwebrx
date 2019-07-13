#!/bin/bash
set -euxo pipefail

function cmakebuild() {
  cd $1
  mkdir build
  cd build
  cmake ..
  make
  make install
  cd ../..
  rm -rf $1
}

cd /tmp

STATIC_PACKAGES="sox fftw python3 netcat-openbsd libsndfile lapack libusb qt5-qtbase qt5-qtmultimedia qt5-qtserialport"
BUILD_PACKAGES="git libsndfile-dev fftw-dev cmake ca-certificates make gcc musl-dev g++ lapack-dev linux-headers autoconf automake libtool texinfo gfortran libusb-dev qt5-qtbase-dev qt5-qtmultimedia-dev qt5-qtserialport-dev asciidoctor asciidoc"

apk add --no-cache $STATIC_PACKAGES
apk add --no-cache --virtual .build-deps $BUILD_PACKAGES

git clone https://git.code.sf.net/p/itpp/git itpp
cmakebuild itpp

git clone https://github.com/jketterl/csdr.git -b 48khz_filter
cd csdr
patch -Np1 <<'EOF'
--- a/csdr.c
+++ b/csdr.c
@@ -38,6 +38,7 @@ SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 #include <sys/time.h>
 #include <sys/types.h>
 #include <sys/stat.h>
+#include <sys/select.h>
 #include <fcntl.h>
 #include <sys/ioctl.h>
 #include <unistd.h>
diff --git a/ddcd_old.h b/ddcd_old.h
index af4cfb5..b70092b 100644
--- a/ddcd_old.h
+++ b/ddcd_old.h
@@ -19,6 +19,7 @@
 #include <stdarg.h>
 #include <sys/stat.h>
 #include <semaphore.h>
+#include <sys/select.h>
 
 typedef struct client_s
 {
diff --git a/nmux.h b/nmux.h
index 038bc51..079e416 100644
--- a/nmux.h
+++ b/nmux.h
@@ -11,6 +11,7 @@
 #include <arpa/inet.h>
 #include <sys/socket.h>
 #include <netinet/in.h>
+#include <sys/select.h>
 #include "tsmpool.h"
 
 #define MSG_START "nmux: "
EOF
make
make install
cd ..
rm -rf csdr

git clone https://github.com/szechyjs/mbelib.git
cmakebuild mbelib
if [ -d "/usr/local/lib64" ]; then
    # no idea why it's put into there now. alpine does not handle it correctly, so move it.
    mv /usr/local/lib64/libmbe* /usr/local/lib
fi

git clone https://github.com/jketterl/digiham.git
cmakebuild digiham

git clone https://github.com/f4exb/dsd.git
cmakebuild dsd

WSJT_DIR=wsjtx-2.0.1
WSJT_TGZ=${WSJT_DIR}.tgz
wget http://physics.princeton.edu/pulsar/k1jt/$WSJT_TGZ
tar xvfz $WSJT_TGZ
cmakebuild $WSJT_DIR

apk del .build-deps
