class Member :

    def __init__(self, id, uid, pw, name, role="user", active=True) :
        self.id = id  # DB의 PK -> AUTO_INCREMENT 자동번호 생성
        self.uid = uid  # 아이디
        self.pw = pw  # 비밀번호
        self.name = name  # 이름
        self.role = role  # 권한
        self.active = active  # 활성화 여부

    @classmethod
    def from_db(cls, row: dict) :

        if not row :
            return None

        return cls(
            id=row.get('id'),  # id : 2
            uid=row.get('uid'), # uid : kkw
            pw=row.get('password'),  # password : 1111
            name=row.get('name'),    # name : 김기원
            role=row.get('role'),    # role : admin
            active=bool(row.get('active')) # active : 1 => True
        )

    def is_admin(self) :
        return self.role == "admin"

    def __str__(self) :
        return f"{self.name}({self.uid}:{self.pw}) [{self.role}]"