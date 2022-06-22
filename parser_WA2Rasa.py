import sys
from ibm_watson import AssistantV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import argparse
import yaml
from yaml.resolver import BaseResolver
import json

class MyDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(MyDumper, self).increase_indent(flow, False)

class AsLiteral(str):
  pass

def represent_literal(dumper, data):
  return dumper.represent_scalar(BaseResolver.DEFAULT_SCALAR_TAG,
      data, style="|")

yaml.add_representer(AsLiteral, represent_literal)

def assistant_instance_connection(api_key, service_url):
    authenticator = IAMAuthenticator(api_key)
    assistant = AssistantV1(
        version='2020-04-01',
        authenticator = authenticator
    )

    assistant.set_service_url(service_url)
    return assistant

def read_workspace(assistant_id, assistant):
    
    skill = assistant.get_workspace(
            workspace_id=assistant_id,
            export=True
        ).get_result()
        
    return skill

def clean_example(example):
    return example.replace("'", "").replace('"', '').replace(":", "")

def parser_intents(intents):
    
    for i, intent in enumerate(intents):
        clean_examples = [clean_example(example["text"]) for example in intent["examples"]]
        # literal_string = "\n- ".join(clean_examples)
        intents[i]["examples"] = clean_examples # AsLiteral(literal_string)
        if type(intent.get("description")) == str:
            del intents[i]["description"]
    return intents

def parser_entities(entities):
    obj_entities = []
    for entity in entities:
        entity_name = entity["entity"]
        synonyms_any = []
        regex_any = []
        synonyms_count = 0
        regex_count = 0
        for value in entity["values"]:
            if value["type"] == "synonyms":
                synonyms_count += 1
                synonyms_any += value["synonyms"] + [value["value"]]
            if value["type"] == "patterns":
                regex_count += 1
                regex_any += value['patterns']
        if synonyms_count > 0:
            item = {"synonym": f'{entity_name}',
                    "examples": synonyms_any}
            obj_entities.append(item)
        if regex_count > 0:
            item = {"regex": f'{entity_name}',
                    "examples": regex_any}
            obj_entities.append(item)
    return obj_entities

def main(args):
    assistant = assistant_instance_connection(
                    api_key=args.api_key, 
                    service_url=args.service_url
                )
    skill = read_workspace(
                assistant_id=args.assistant_id,
                assistant=assistant
            )
    del skill["dialog_nodes"]
    intents = parser_intents(skill["intents"])
    entities = parser_entities(skill["entities"])
    # print(json.dumps(entities, sort_keys=False, indent=4, ensure_ascii=False))
    nlu_yml_obj = {
        "version": "3.1",
        "nlu": intents + entities
    }
    with open('data/nlu.yml', 'w') as outfile:
        yaml.dump(nlu_yml_obj, 
                 outfile, 
                 allow_unicode=True, 
                 Dumper=MyDumper,
                 sort_keys=False)
    

if __name__=="__main__":
    arguments = argparse.ArgumentParser()
    arguments.add_argument('-key', 
                        '--api_key', 
                        type=str, 
                        help='O API KEY do workspace WA.')
    arguments.add_argument('-url', 
                        '--service_url',
                        type=str,
                        help='A URL do serviço WA')

    arguments.add_argument('-skill', 
                        '--assistant_id',
                        type=str,
                        help='O skill id do skill dentro do workspace em questão.')
    args = arguments.parse_args()
    main(args)