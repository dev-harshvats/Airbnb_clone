# Airbnb clone backend on AWS: one EC2 instance (FastAPI behind nginx) + one S3 bucket for uploaded photos.
#
#   terraform init
#   terraform apply
#
# That's it: the instance clones the repo, installs everything, applies the migrations, seeds the demo
# data and starts the API by itself (give it ~5 minutes). See the `next_steps` output afterwards.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.0" }
    random = { source = "hashicorp/random", version = "~> 3.6" }
    tls    = { source = "hashicorp/tls", version = "~> 4.0" }
    local  = { source = "hashicorp/local", version = "~> 2.5" }
  }
}

# ---------------------------------------------------------------------------------------------
# Settings (override with -var, or a terraform.tfvars file; every one has a working default)
# ---------------------------------------------------------------------------------------------

variable "region" {
  description = "AWS region. Mumbai suits an India-only app."
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Name prefix for every resource."
  type        = string
  default     = "airbnb-clone"
}

variable "instance_type" {
  description = "t3.small (2 GB) is comfortable; t3.micro (1 GB) works for a demo."
  type        = string
  default     = "t3.small"
}

variable "disk_gb" {
  description = "Root disk size. The SQLite database and the demo photos live here."
  type        = number
  default     = 20
}

variable "repo_url" {
  description = "Git repository the server clones. For a private repo use https://<user>:<token>@github.com/..."
  type        = string
  default     = "https://github.com/dev-harshvats/Airbnb_clone.git"
  sensitive   = true
}

variable "repo_branch" {
  type    = string
  default = "main"
}

variable "frontend_origin" {
  description = "Where the website is served from (used for CORS), e.g. https://my-app.vercel.app"
  type        = string
  default     = "http://localhost:3000"
}

variable "cookie_secure" {
  description = "Mark the login cookie Secure. Keep true when the website is on https (Vercel is)."
  type        = bool
  default     = true
}

variable "auth_rate_limit" {
  description = "Login/signup attempts per client IP. Behind a website proxy every visitor shares one IP, so this is looser than the 5/minute default."
  type        = string
  default     = "30/minute"
}

variable "seed_demo_data" {
  description = "Fill the database with the demo listings, users and bookings on first boot."
  type        = bool
  default     = true
}

variable "ssh_cidr" {
  description = "Who may SSH in. Narrow this to your own IP, e.g. 203.0.113.7/32."
  type        = string
  default     = "0.0.0.0/0"
}

variable "force_destroy_bucket" {
  description = "Let `terraform destroy` delete the bucket even if it still holds uploaded photos."
  type        = bool
  default     = false
}

# ---------------------------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------------------------

provider "aws" {
  region = var.region
  default_tags {
    tags = { Project = var.project, ManagedBy = "terraform" }
  }
}

# Latest Amazon Linux 2023 (has the AWS CLI, and python3.11 in its repos).
data "aws_ssm_parameter" "ami" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

# The account's default network. If you deleted it, create one with `aws ec2 create-default-vpc`.
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ---------------------------------------------------------------------------------------------
# Secrets and names
# ---------------------------------------------------------------------------------------------

# Signs the login tokens. Kept in SSM Parameter Store (encrypted); the server reads it at boot with
# its own role, so it never appears in the instance's user-data.
resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

resource "aws_ssm_parameter" "jwt_secret" {
  name  = "/${var.project}/jwt_secret"
  type  = "SecureString"
  value = random_password.jwt_secret.result
}

resource "random_id" "suffix" {
  byte_length = 4
}

# SSH key pair, generated here. The private key is written next to this file.
resource "tls_private_key" "ssh" {
  algorithm = "ED25519"
}

resource "aws_key_pair" "ssh" {
  key_name   = "${var.project}-key"
  public_key = tls_private_key.ssh.public_key_openssh
}

resource "local_sensitive_file" "ssh_key" {
  content         = tls_private_key.ssh.private_key_openssh
  filename        = "${path.module}/${var.project}-key.pem"
  file_permission = "0400"
}

# ---------------------------------------------------------------------------------------------
# S3: uploaded listing photos
# ---------------------------------------------------------------------------------------------

resource "aws_s3_bucket" "media" {
  bucket        = "${var.project}-media-${random_id.suffix.hex}"
  force_destroy = var.force_destroy_bucket
}

resource "aws_s3_bucket_ownership_controls" "media" {
  bucket = aws_s3_bucket.media.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# Public *policies* are allowed (so the photos can be read), public ACLs are not.
resource "aws_s3_bucket_public_access_block" "media" {
  bucket                  = aws_s3_bucket.media.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = false
  restrict_public_buckets = false
}

# Only uploads/* is readable by the world (browsers load listing photos straight from S3).
resource "aws_s3_bucket_policy" "media_public_read" {
  bucket     = aws_s3_bucket.media.id
  depends_on = [aws_s3_bucket_public_access_block.media]
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadUploads"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.media.arn}/uploads/*"
    }]
  })
}

# ---------------------------------------------------------------------------------------------
# IAM: what the server is allowed to do (write photos, read its one secret)
# ---------------------------------------------------------------------------------------------

resource "aws_iam_role" "server" {
  name = "${var.project}-server"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "server" {
  name = "media-and-secret"
  role = aws_iam_role.server.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:DeleteObject"]
        Resource = "${aws_s3_bucket.media.arn}/uploads/*"
      },
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter"]
        Resource = aws_ssm_parameter.jwt_secret.arn
      },
    ]
  })
}

resource "aws_iam_instance_profile" "server" {
  name = "${var.project}-server"
  role = aws_iam_role.server.name
}

# ---------------------------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------------------------

resource "aws_security_group" "server" {
  name        = "${var.project}-server"
  description = "Web traffic and SSH"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "HTTPS (for when you add a certificate)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ---------------------------------------------------------------------------------------------
# The server
# ---------------------------------------------------------------------------------------------

locals {
  # Runs once, on first boot. Uses plain $VAR (no braces) so Terraform leaves the shell alone.
  user_data = <<-EOT
    #!/bin/bash
    set -euxo pipefail
    exec > >(tee /var/log/airbnb-setup.log) 2>&1

    dnf install -y git python3.11 python3.11-pip python3.11-devel gcc nginx

    # A system user that owns the code and the database; nothing here runs as root.
    useradd --system --home-dir /opt/airbnb --shell /sbin/nologin airbnb
    mkdir -p /opt/airbnb/data
    chown -R airbnb:airbnb /opt/airbnb

    runuser -u airbnb -- git clone --depth 1 --branch ${var.repo_branch} '${var.repo_url}' /opt/airbnb/app
    cd /opt/airbnb/app/backend
    runuser -u airbnb -- python3.11 -m venv .venv
    runuser -u airbnb -- .venv/bin/pip install --quiet --upgrade pip
    runuser -u airbnb -- .venv/bin/pip install --quiet -e ".[aws]"

    # The login-token secret comes from SSM. The role can take a moment to become active, so retry.
    JWT_SECRET=""
    for attempt in 1 2 3 4 5 6 7 8 9 10; do
      JWT_SECRET=$(aws ssm get-parameter --name '${aws_ssm_parameter.jwt_secret.name}' --with-decryption \
        --query Parameter.Value --output text --region ${var.region}) && break
      sleep 10
    done
    test -n "$JWT_SECRET"

    cat > .env <<ENVFILE
    ENV=production
    DATABASE_URL=sqlite:////opt/airbnb/data/airbnb.db
    MEDIA_DIR=media
    STORAGE_BACKEND=s3
    S3_BUCKET=${aws_s3_bucket.media.bucket}
    S3_REGION=${var.region}
    CORS_ORIGINS=["${var.frontend_origin}"]
    JWT_SECRET=$JWT_SECRET
    COOKIE_SECURE=${var.cookie_secure}
    TRUST_PROXY_HEADERS=false
    AUTH_RATE_LIMIT=${var.auth_rate_limit}
    ENVFILE
    chown airbnb:airbnb .env
    chmod 600 .env

    runuser -u airbnb -- .venv/bin/python -m alembic upgrade head
    %{if var.seed_demo_data~}
    runuser -u airbnb -- .venv/bin/python -m app.seed
    %{endif~}

    # The API: one process (SQLite and the in-memory rate limiter both assume a single worker).
    cat > /etc/systemd/system/airbnb-api.service <<UNIT
    [Unit]
    Description=Airbnb clone API
    After=network.target

    [Service]
    User=airbnb
    WorkingDirectory=/opt/airbnb/app/backend
    ExecStart=/opt/airbnb/app/backend/.venv/bin/uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --workers 1 --no-access-log --no-proxy-headers
    Restart=always
    RestartSec=3
    NoNewPrivileges=true

    [Install]
    WantedBy=multi-user.target
    UNIT

    # nginx on port 80 in front of it (5 MB photo uploads plus a little room for the form).
    cat > /etc/nginx/nginx.conf <<NGINX
    user nginx;
    worker_processes auto;
    pid /run/nginx.pid;
    error_log /var/log/nginx/error.log;
    events { worker_connections 1024; }
    http {
      include /etc/nginx/mime.types;
      server_tokens off;
      client_max_body_size 6m;
      server {
        listen 80 default_server;
        server_name _;
        location / {
          proxy_pass http://127.0.0.1:8000;
          proxy_set_header Host \$host;
          proxy_set_header X-Forwarded-For \$remote_addr;
          proxy_set_header X-Forwarded-Proto \$scheme;
          proxy_read_timeout 60s;
        }
      }
    }
    NGINX

    # One command to ship a new version later:  sudo airbnb-deploy
    cat > /usr/local/bin/airbnb-deploy <<'DEPLOY'
    #!/bin/bash
    set -euo pipefail
    cd /opt/airbnb/app
    runuser -u airbnb -- git pull --ff-only
    cd backend
    runuser -u airbnb -- .venv/bin/pip install --quiet -e ".[aws]"
    runuser -u airbnb -- .venv/bin/python -m alembic upgrade head
    systemctl restart airbnb-api
    DEPLOY
    chmod +x /usr/local/bin/airbnb-deploy

    systemctl daemon-reload
    systemctl enable --now airbnb-api nginx
    echo "airbnb setup finished"
  EOT
}

resource "aws_instance" "server" {
  ami                    = data.aws_ssm_parameter.ami.value
  instance_type          = var.instance_type
  key_name               = aws_key_pair.ssh.key_name
  subnet_id              = data.aws_subnets.default.ids[0]
  vpc_security_group_ids = [aws_security_group.server.id]
  iam_instance_profile   = aws_iam_instance_profile.server.name

  associate_public_ip_address = true # reachable for setup before the Elastic IP is attached

  user_data                   = local.user_data
  user_data_replace_on_change = true

  metadata_options {
    http_tokens = "required" # IMDSv2 only
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = var.disk_gb
    encrypted   = true
  }

  tags = { Name = "${var.project}-api" }

  depends_on = [aws_iam_role_policy.server]
}

# A fixed public address, so the website's API_ORIGIN never changes.
resource "aws_eip" "server" {
  domain   = "vpc"
  instance = aws_instance.server.id
  tags     = { Name = "${var.project}-api" }
}

# ---------------------------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------------------------

output "api_url" {
  description = "Base URL of the API. Set this as API_ORIGIN on the website."
  value       = "http://${aws_eip.server.public_ip}"
}

output "health_check" {
  value = "http://${aws_eip.server.public_ip}/api/v1/health"
}

output "api_docs" {
  value = "http://${aws_eip.server.public_ip}/api/docs"
}

output "ssh_command" {
  value = "ssh -i ${local_sensitive_file.ssh_key.filename} ec2-user@${aws_eip.server.public_ip}"
}

output "media_bucket" {
  value = aws_s3_bucket.media.bucket
}

output "next_steps" {
  value = <<-EOT

    1. Wait about 5 minutes for the first boot to finish, then open the health_check URL: it should say {"status":"ok"}.
       (Watch progress with:  ssh -i ${local_sensitive_file.ssh_key.filename} ec2-user@${aws_eip.server.public_ip} 'tail -f /var/log/airbnb-setup.log')
    2. On the website host (e.g. Vercel) set the environment variable  API_ORIGIN = http://${aws_eip.server.public_ip}  and redeploy it.
    3. Ship a new backend version later:  ssh in, then  sudo airbnb-deploy
  EOT
}
