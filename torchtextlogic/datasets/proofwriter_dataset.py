import os
from typing import List, Tuple, Union

from datasets.base import AbstractProofQADataset
from torchtextlogic.datasets.exceptions import (
    AbductionClosedWorldAssumptionError,
    DatasetNameError,
    SplitSetError,
    TaskError,
)
from torchtextlogic.datasets.utils import (
    DATASETS_FOLDER,
    SPLIT_SETS,
    download_dataset,
    read_jsonl,
)

PROOFWRITER_DATASET_ZIP_URL = (
    "https://www.dropbox.com/s/5dpm2yjcm5h9hsd/proofwriter_dataset.zip?dl=1"
)
PROOFWRITER_DATASET = "proofwriter_dataset"
PROOFWRITER_SUB_DATASETS = [
    "birds-electricity",
    "depth-0",
    "depth-1",
    "depth-2",
    "depth-3",
    "depth-3ext",
    "depth-3ext-NatLang",
    "depth-5",
    "NatLang",
]
PROOFWRITER_TASKS = [
    "proof_generation_all",
    "proof_generation_iter",
    "implication_enumeration",
    "abduction",
]
PROOFWRITER_DATASET_FOLDER = f"{DATASETS_FOLDER}/{PROOFWRITER_DATASET}"
PROOFWRITER_LABEL_TO_ID = {"False": 0, "True": 1, "Unknown": 2}
PROOFWRITER_ID_TO_LABEL = {0: "False", 1: "True", 2: "Unknown"}


class ProofWriterDataset(AbstractProofQADataset):
    def __init__(
        self,
        dataset_name: str,
        split_set: str,
        task: str,
        open_world_assumption: bool = False,
    ) -> None:
        try:
            if dataset_name not in PROOFWRITER_SUB_DATASETS:
                raise DatasetNameError()
            if split_set != "test" and dataset_name == "birds-electricity":
                raise SplitSetError(["test"])

            if split_set == "val":
                split_set = "dev"
            elif split_set not in SPLIT_SETS:
                raise SplitSetError(SPLIT_SETS)

            if task not in PROOFWRITER_TASKS:
                raise TaskError()

            if not os.path.exists(PROOFWRITER_DATASET_FOLDER):
                download_dataset(PROOFWRITER_DATASET_ZIP_URL, PROOFWRITER_DATASET)

            self.dataset_name = dataset_name
            self.split_set = split_set
            self.task = task
            self.world_assumption = "CWA"

            if open_world_assumption:
                self.world_assumption = "OWA"

            if self.world_assumption == "CWA" and self.task == "abduction":
                raise AbductionClosedWorldAssumptionError()

            if self.task == "proof_generation_all":
                self.dataset_path = f"{PROOFWRITER_DATASET_FOLDER}/{self.world_assumption}/{self.dataset_name}/meta-{self.split_set}.jsonl"
                self.__read_dataset_proof_generation_all(
                    "triples", "rules", "questions", "answer", "proofsWithIntermediates"
                )
            elif self.task == "proof_generation_iter":
                self.dataset_path = f"{PROOFWRITER_DATASET_FOLDER}/{self.world_assumption}/{self.dataset_name}/meta-stage-{self.split_set}.jsonl"
                self.__read_dataset_proof_generation_iter(
                    "triples", "rules", "allInferences"
                )
            elif self.task == "implication_enumeration":
                self.dataset_path = f"{PROOFWRITER_DATASET_FOLDER}/{self.world_assumption}/{self.dataset_name}/meta-{self.split_set}.jsonl"
                self.__read_dataset_implication_enumeration()
            elif self.task == "abduction":
                self.dataset_path = f"{PROOFWRITER_DATASET_FOLDER}/{self.world_assumption}/{self.dataset_name}/meta-abduct-{self.split_set}.jsonl"
                self.__read_dataset_abduction()

        except DatasetNameError as err:
            print(err.message)
            print(f"The ProofWriter datasets are: {PROOFWRITER_SUB_DATASETS}")
        except SplitSetError as err:
            print(err.message)
        except TaskError as err:
            print(err.message)
            print(f"The ProofWriter tasks are: {PROOFWRITER_TASKS}")
        except AbductionClosedWorldAssumptionError as err:
            print(err.message)

    def __read_dataset_proof_generation_all(
        self,
        triples_key: str,
        rules_key: str,
        questions_key: str,
        answers_key: str,
        proofs_key: str,
    ) -> Tuple[List[str], List[str], List[str]]:
        data = read_jsonl(self.dataset_path)
        contexts_list = []
        questions_list = []
        labels_list = []

        for i in data:
            triples = []
            rules = []
            questions = []
            answers_with_proofs = []

            for t, val in i[triples_key].items():
                triples.append(f"{t}: {val['text']}")

            for r, val in i[rules_key].items():
                rules.append(f"{r}: {val['text']}")

            for q in i[questions_key].values():
                questions.append(q["question"])
                if proofs_key in q:
                    tmp_proof = ""
                    for nbr, p in enumerate(q[proofs_key]):
                        tmp_proof += f"Proof {nbr}: {p['representation']} ; "
                        if len(p["intermediates"]) > 0:
                            tmp_proof += "with "
                            for intr, val in p["intermediates"].items():
                                tmp_proof += f"{intr} = {val['text']} ; "
                        tmp_proof += "\n"

                answers_with_proofs.append(f"Answer: {q[answers_key]}\n{tmp_proof}")

            tmp_context = triples + rules

            for q, ap in zip(questions, answers_with_proofs):
                contexts_list.append("\n".join(tmp_context))
                questions_list.append(q)
                labels_list.append(ap)

        return contexts_list, questions_list, labels_list

    def __read_dataset_proof_generation_iter(
        self, triples_key: str, rules_key: str, proofs_key: str
    ) -> Tuple[List[str], List[str]]:
        data = read_jsonl(self.dataset_path)
        contexts_list = []
        labels_list = []

        for i in data:
            triples = []
            rules = []
            inferences = []

            for t, val in i[triples_key].items():
                triples.append(f"{t}: {val['text']}")
            for r, val in i[rules_key].items():
                rules.append(f"{r}: {val['text']}")
            for val in i[proofs_key]:
                inferences.append(val["text"])

            tmp_context = triples + rules
            contexts_list.append("\n".join(tmp_context))
            labels_list.append("\n".join(inferences))

        return contexts_list, labels_list

    def __read_dataset_implication_enumeration(self):
        data = read_jsonl(self.dataset_path)

    def __read_dataset_abduction(self):
        data = read_jsonl(self.dataset_path)

    def __getitem__(self, index: int) -> Union[Tuple[str, str, str], Tuple[str, str]]:
        pass

    def __str__(self) -> str:
        pass

    def __len__(self) -> int:
        pass
