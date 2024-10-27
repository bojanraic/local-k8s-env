#!/bin/bash
set -e

check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "$1 is required but not installed."
        return 1
    fi
}

install_brew_if_missing() {
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
}

install_dependencies_macos() {
    install_brew_if_missing

    # Install required tools using Homebrew
    TOOLS="kubectl k3d helm helmfile mkcert yq python@3.12 go-task"
    for tool in $TOOLS; do
        if ! brew list $tool &>/dev/null; then
            echo "Installing $tool..."
            brew install $tool
        fi
    done

    # Install Helm plugins
    if ! helm plugin list | grep -q "diff"; then
        helm plugin install https://github.com/databus23/helm-diff
    fi
}

install_dependencies_linux() {
    # Create temporary directory
    TMP_DIR=".local/tmp"
    mkdir -p "$TMP_DIR"
    
    # Install required tools by downloading binaries from GitHub
    TOOLS=("kubectl" "k3d" "helm" "helmfile" "mkcert" "yq" "python" "go-task" "jq" "libnss3-tools" "kubeconform")
    for tool in "${TOOLS[@]}"; do
        case $tool in
            kubeconform)
                if command -v kubeconform &> /dev/null; then
                    echo "✅ kubeconform is already installed"
                    continue
                fi
                KUBECONFORM_VERSION=$(curl -s https://api.github.com/repos/yannh/kubeconform/releases/latest | grep tag_name | cut -d '"' -f 4)
                KUBECONFORM_URL="https://github.com/yannh/kubeconform/releases/download/${KUBECONFORM_VERSION}/kubeconform-linux-amd64.tar.gz"
                echo "🔗 Download URL: $KUBECONFORM_URL"
                curl -Lo "$TMP_DIR/kubeconform.tar.gz" "$KUBECONFORM_URL"
                tar xf "$TMP_DIR/kubeconform.tar.gz" -C "$TMP_DIR"
                chmod +x "$TMP_DIR/kubeconform"
                sudo mv "$TMP_DIR/kubeconform" /usr/local/bin/
                ;;
            python)
                if command -v python3 &> /dev/null; then
                    echo "✅ python3 is already installed"
                    continue
                else
                    echo "Installing python3..."
                    sudo apt-get update
                    sudo apt-get install -y python3
                fi
                ;;
            go-task)
                if command -v task &> /dev/null; then
                    echo "✅ task is already installed"
                    continue
                fi
                ;;
            libnss3-tools)
                if dpkg -s libnss3-tools &> /dev/null; then
                    echo "✅ libnss3-tools is already installed"
                    continue
                fi
                ;;
            *)
                if command -v $tool &> /dev/null; then
                    echo "✅ $tool is already installed"
                    continue
                fi
                ;;
        esac
        echo "📥 Downloading $tool..."
        case $tool in
            jq)
                JQ_VERSION=$(curl -s https://api.github.com/repos/jqlang/jq/releases/latest | grep tag_name | cut -d '"' -f 4)
                VERSION_NUM=${JQ_VERSION#jq-}  # Remove 'jq-' prefix from version
                JQ_URL="https://github.com/jqlang/jq/releases/download/${JQ_VERSION}/jq-linux-amd64"
                echo "🔗 Download URL: $JQ_URL"
                curl -Lo "$TMP_DIR/jq" "$JQ_URL"
                chmod +x "$TMP_DIR/jq"
                sudo mv "$TMP_DIR/jq" /usr/local/bin/
                ;;
            kubectl)
                KUBECTL_VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt)
                KUBECTL_URL="https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl"
                echo "🔗 Download URL: $KUBECTL_URL"
                curl -Lo "$TMP_DIR/kubectl" "$KUBECTL_URL"
                chmod +x "$TMP_DIR/kubectl"
                sudo mv "$TMP_DIR/kubectl" /usr/local/bin/
                ;;

            k3d)
                K3D_VERSION=$(curl -s https://api.github.com/repos/k3d-io/k3d/releases/latest | grep tag_name | cut -d '"' -f 4)
                K3D_URL="https://github.com/k3d-io/k3d/releases/download/${K3D_VERSION}/k3d-linux-amd64"
                echo "🔗 Download URL: $K3D_URL"
                curl -Lo "$TMP_DIR/k3d" "$K3D_URL"
                chmod +x "$TMP_DIR/k3d"
                sudo mv "$TMP_DIR/k3d" /usr/local/bin/
                ;;

            helm)
                HELM_SCRIPT_URL="https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3"
                echo "🔗 Download URL: $HELM_SCRIPT_URL"
                curl -fsSL -o "$TMP_DIR/get_helm.sh" "$HELM_SCRIPT_URL"
                chmod 700 "$TMP_DIR/get_helm.sh"
                HELM_INSTALL_DIR=/usr/local/bin "$TMP_DIR/get_helm.sh"
                ;;

            helmfile)
                HELMFILE_VERSION=$(curl -s https://api.github.com/repos/helmfile/helmfile/releases/latest | grep tag_name | cut -d '"' -f 4)
                VERSION_NUM=${HELMFILE_VERSION#v}
                HELMFILE_URL="https://github.com/helmfile/helmfile/releases/download/${HELMFILE_VERSION}/helmfile_${VERSION_NUM}_linux_amd64.tar.gz"
                echo "🔗 Download URL: $HELMFILE_URL"
                curl -Lo "$TMP_DIR/helmfile.tar.gz" "$HELMFILE_URL"
                tar xf "$TMP_DIR/helmfile.tar.gz" -C "$TMP_DIR"
                chmod +x "$TMP_DIR/helmfile"
                sudo mv "$TMP_DIR/helmfile" /usr/local/bin/
                ;;

            mkcert)
                MKCERT_VERSION=$(curl -s https://api.github.com/repos/FiloSottile/mkcert/releases/latest | grep tag_name | cut -d '"' -f 4)
                MKCERT_URL="https://github.com/FiloSottile/mkcert/releases/download/${MKCERT_VERSION}/mkcert-${MKCERT_VERSION}-linux-amd64"
                echo "🔗 Download URL: $MKCERT_URL"
                curl -Lo "$TMP_DIR/mkcert" "$MKCERT_URL"
                chmod +x "$TMP_DIR/mkcert"
                sudo mv "$TMP_DIR/mkcert" /usr/local/bin/
                ;;

            yq)
                YQ_VERSION=$(curl -s https://api.github.com/repos/mikefarah/yq/releases/latest | grep tag_name | cut -d '"' -f 4)
                YQ_URL="https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/yq_linux_amd64"
                echo "🔗 Download URL: $YQ_URL"
                curl -Lo "$TMP_DIR/yq" "$YQ_URL"
                chmod +x "$TMP_DIR/yq"
                sudo mv "$TMP_DIR/yq" /usr/local/bin/
                ;;

            task)
                TASK_VERSION=$(curl -s https://api.github.com/repos/go-task/task/releases/latest | grep tag_name | cut -d '"' -f 4)
                TASK_URL="https://github.com/go-task/task/releases/download/${TASK_VERSION}/task_linux_amd64.tar.gz"
                echo "🔗 Download URL: $TASK_URL"
                curl -Lo "$TMP_DIR/task.tar.gz" "$TASK_URL"
                tar xf "$TMP_DIR/task.tar.gz" -C "$TMP_DIR"
                chmod +x "$TMP_DIR/task"
                sudo mv "$TMP_DIR/task" /usr/local/bin/
                ;;
            kubeconform)
                if command -v kubeconform &> /dev/null; then
                    echo "✅ kubeconform is already installed"
                    continue
                fi
                KUBECONFORM_VERSION=$(curl -s https://api.github.com/repos/yannh/kubeconform/releases/latest | grep tag_name | cut -d '"' -f 4)
                KUBECONFORM_URL="https://github.com/yannh/kubeconform/releases/download/${KUBECONFORM_VERSION}/kubeconform-linux-amd64.tar.gz"
                echo "🔗 Download URL: $KUBECONFORM_URL"
                curl -Lo "$TMP_DIR/kubeconform.tar.gz" "$KUBECONFORM_URL"
                tar xf "$TMP_DIR/kubeconform.tar.gz" -C "$TMP_DIR"
                chmod +x "$TMP_DIR/kubeconform"
                sudo mv "$TMP_DIR/kubeconform" /usr/local/bin/
                ;;
            libnss3-tools)
                if dpkg -s libnss3-tools &> /dev/null; then
                    echo "✅ libnss3-tools is already installed"
                    continue
                else
                    echo "Installing libnss3-tools..."
                    sudo apt-get update
                    sudo apt-get install -y libnss3-tools
                fi
                ;;
            python)
                if command -v python3 &> /dev/null; then
                    echo "✅ python3 is already installed"
                    continue
                else
                    echo "Installing python3..."
                    sudo apt-get update
                    sudo apt-get install -y python3
                fi
                ;;
        esac
    done

    # Clean up temporary directory
    rm -rf "$TMP_DIR"
    
    # Install Helm plugins
    if ! helm plugin list | grep -q "diff"; then
        helm plugin install https://github.com/databus23/helm-diff
    fi
}

# Check for required commands
REQUIRED_COMMANDS="python3 task kubectl k3d helm helmfile mkcert yq kubeconform"
MISSING_COMMANDS=0

for cmd in $REQUIRED_COMMANDS; do
    if ! check_command $cmd; then
        MISSING_COMMANDS=1
    fi
done

if [ $MISSING_COMMANDS -eq 1 ]; then
    echo "Installing missing dependencies..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        install_dependencies_macos
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        install_dependencies_linux
    else
        echo "Unsupported OS type: $OSTYPE"
        exit 1
    fi
fi

echo "All dependencies are installed."