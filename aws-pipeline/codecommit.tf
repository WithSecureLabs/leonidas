resource "aws_codecommit_repository" "repo" {
  repository_name = "Leonidas"
  description     = "CodeBuild Repository containing attacker actions and all the infrastructure"
}

resource "aws_iam_user" "codecommit_user" {
  name = "codecommituser-${lower(terraform.workspace)}"
  path = "/${lower(terraform.workspace)}/"
  force_destroy = true
}

resource "aws_iam_user_ssh_key" "codecommit_user_key" {
  username   = "${aws_iam_user.codecommit_user.name}"
  encoding   = "SSH"
  public_key = "${file(var.codecommit_ssh_key)}"
  status     = "Active"
}

resource "aws_iam_group" "codecommit_group" {
  name = "codecommit-${lower(terraform.workspace)}"
  path = "/${lower(terraform.workspace)}/"
}

resource "aws_iam_group_membership" "codecommit_group_membership" {
  name = "codecommit-group-membership-${lower(terraform.workspace)}"

  users = [
    "${aws_iam_user.codecommit_user.name}",
  ]

  group = "${aws_iam_group.codecommit_group.name}"
}

resource "aws_iam_policy" "codecommit_policy" {
  name        = "codecommit-policy-${lower(terraform.workspace)}"
  path        = "/${lower(terraform.workspace)}/"
  description = "CodeCommit policy for ${lower(terraform.workspace)}"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AccessSpecificRepo",
            "Effect": "Allow",
            "Action": [
              "codecommit:GitPull",
              "codecommit:GitPush"
            ],
            "Resource": "arn:aws:codecommit:*:*:${aws_codecommit_repository.repo.repository_name}"
        },
        {
            "Sid": "ViewRepositoriesConsole",
            "Effect": "Allow",
            "Action": [
                "codecommit:Get*",
                "codecommit:BatchGetRepositories",
                "codecommit:List*"
            ],
            "Resource": "*"
        },
        {
            "Sid": "ManageRepoCredentials",
            "Effect": "Allow",
            "Action": [
                "iam:*ServiceSpecificCredential*",
                "iam:*SSHPublicKey*",
                "iam:GetUser"
            ],
            "Resource": "${aws_iam_user.codecommit_user.arn}"
        },
        {
            "Sid": "SelfEnumerate",
            "Effect": "Allow",
            "Action": [
                "iam:GetUser",
                "iam:GetUserPolicy",
                "iam:ListAttachedUserPolicies",
                "iam:ListGroupsForUser"
            ],
            "Resource": "${aws_iam_user.codecommit_user.arn}"
        },
        {
          "Sid": "GroupEnumerate",
          "Effect": "Allow",
          "Action": [
              "iam:GetGroupPolicy",
              "iam:ListGroupPolicies",
              "iam:ListAttachedGroupPolicies"
          ],
          "Resource": "${aws_iam_group.codecommit_group.arn}"
        },
        {
          "Sid": "GetPolicyDetails",
          "Effect": "Allow",
          "Action": [
              "iam:GetPolicy"
          ],
          "Resource": "*"
        }
    ]
}
EOF
}

resource "aws_iam_policy_attachment" "codecommit-group-policy-attach" {
  name       = "codecommit-group-policy-attach"
  users      = ["${aws_iam_user.codecommit_user.name}"]
  policy_arn = "${aws_iam_policy.codecommit_policy.arn}"
}

